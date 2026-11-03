"""Read-only S3 operations, signed for the hostname but connected to a pinned public IP."""

import base64
import hashlib
import ipaddress
import json
import mimetypes
import socket
from urllib.parse import quote, urlencode, urlsplit
from xml.etree import ElementTree

import httpx
from botocore.auth import S3SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
from cryptography.fernet import Fernet
from fastapi import HTTPException

MEDIA = {"image/jpeg", "image/png", "image/webp", "video/mp4"}
DOCUMENTS = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def cipher(settings):
    key = settings.storage_encryption_key.get_secret_value()
    if not key:
        raise HTTPException(503, "Storage credential encryption is not configured.")
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest()))


def encrypt(settings, access, secret):
    if not access or not secret or len(access) > 256 or len(secret) > 4096:
        raise HTTPException(422, "Both storage credentials are required.")
    return cipher(settings).encrypt(json.dumps([access, secret]).encode()).decode()


def endpoint_address(endpoint):
    try:
        parsed = urlsplit(endpoint)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.port not in {None, 443}
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise ValueError()
        addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
            raise ValueError()
        return parsed.hostname, addresses[0][4][0]
    except (ValueError, OSError) as exc:
        raise HTTPException(422, "Use a public HTTPS storage endpoint on port 443.") from exc


def check_key(connection, key):
    if (
        not key
        or len(key.encode()) > 1024
        or not key.startswith(connection.prefix)
        or "\x00" in key
        or any(part in {".", ".."} for part in key.split("/"))
    ):
        raise HTTPException(422, "Object is outside the configured folder or has an invalid key.")
    return key


def mime_for(key):
    return mimetypes.guess_type(key)[0] or "application/octet-stream"


class BucketClient:
    def __init__(self, connection, settings):
        self.connection = connection
        self.settings = settings
        self.credentials = Credentials(
            *json.loads(cipher(settings).decrypt(connection.secret.encode()))
        )

    def request(self, method, key="", query=None, etag=None, maximum=2 * 1024 * 1024):
        row = self.connection
        host, address = endpoint_address(row.endpoint)
        path = "/" + row.bucket + ("/" + quote(key, safe="/~-._") if key else "")
        url = f"https://{host}{path}" + ("?" + urlencode(query, quote_via=quote) if query else "")
        headers = {"Host": host}
        if etag:
            headers["If-Match"] = etag
        signed = AWSRequest(method=method, url=url, headers=headers)
        S3SigV4Auth(self.credentials, "s3", row.region).add_auth(signed)
        try:
            with httpx.Client(timeout=60, follow_redirects=False, trust_env=False) as client:
                with client.stream(
                    method,
                    httpx.URL(url).copy_with(host=address),
                    headers=dict(signed.headers),
                    extensions={"sni_hostname": host},
                ) as response:
                    if response.status_code not in {200, 206}:
                        status = response.status_code
                        raise HTTPException(
                            409 if status == 412 else 502,
                            {
                                "code": "object_changed"
                                if status == 412
                                else "storage_access_failed",
                                "upstream_status": status,
                            },
                        )
                    if method == "HEAD":
                        return b"", dict(response.headers)
                    if int(response.headers.get("content-length", "0")) > maximum:
                        raise HTTPException(413, "Remote resource exceeds the permitted size.")
                    content = bytearray()
                    for chunk in response.iter_bytes():
                        content.extend(chunk)
                        if len(content) > maximum:
                            raise HTTPException(413, "Remote resource exceeds the permitted size.")
                    return bytes(content), dict(response.headers)
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(
                502, "Storage is unavailable or returned an invalid response."
            ) from exc

    def objects(self, prefix="", cursor=None, recursive=False):
        prefix = prefix or self.connection.prefix
        if prefix:
            check_key(self.connection, prefix)
        if prefix and not prefix.endswith("/"):
            prefix += "/"
        if not prefix.startswith(self.connection.prefix):
            raise HTTPException(422, "Folder is outside the configured prefix.")
        query = {"list-type": "2", "prefix": prefix, "max-keys": "100", "encoding-type": "url"}
        if not recursive:
            query["delimiter"] = "/"
        if cursor:
            query["continuation-token"] = cursor
        raw, _ = self.request("GET", query=query)
        if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
            raise HTTPException(502, "Invalid storage listing.")
        try:
            root = ElementTree.fromstring(raw)
            from urllib.parse import unquote

            def text(node, name):
                return node.findtext("{*}" + name, "")

            items = [
                {
                    "key": unquote(text(n, "Key")),
                    "size": int(text(n, "Size")),
                    "etag": text(n, "ETag"),
                    "modified_at": text(n, "LastModified"),
                    "mime_type": mime_for(unquote(text(n, "Key"))),
                }
                for n in root.findall("{*}Contents")
            ]
            return {
                "prefix": prefix,
                "folders": [unquote(text(n, "Prefix")) for n in root.findall("{*}CommonPrefixes")],
                "items": items,
                "next_cursor": text(root, "NextContinuationToken") or None,
            }
        except (ElementTree.ParseError, ValueError) as exc:
            raise HTTPException(502, "Invalid storage listing.") from exc

    def download(self, key):
        check_key(self.connection, key)
        mime = mime_for(key)
        if mime not in MEDIA | DOCUMENTS:
            raise HTTPException(415, "Use JPEG, PNG, WebP, MP4, PDF or DOCX.")
        maximum = min(
            self.settings.storage_max_download_bytes,
            (self.settings.max_video_bytes or self.settings.storage_max_download_bytes)
            if mime == "video/mp4"
            else self.settings.max_image_bytes
            if mime in MEDIA
            else 10 * 1024 * 1024,
        )
        _, head = self.request("HEAD", key)
        if int(head.get("content-length", "0")) > maximum:
            raise HTTPException(413, "Remote resource exceeds the permitted size.")
        raw, headers = self.request("GET", key, etag=head.get("etag"), maximum=maximum)
        if not raw or (head.get("etag") and headers.get("etag") != head["etag"]):
            raise HTTPException(409, "Object changed during download or is empty.")
        return (
            raw,
            mime,
            {
                "key": key,
                "etag": headers.get("etag"),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "byte_size": len(raw),
                "modified_at": headers.get("last-modified"),
            },
        )
