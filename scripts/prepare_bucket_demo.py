"""Inventory or upload synthetic fixtures to a private R2/S3 evaluation bucket.

Credentials JSON: endpoint, bucket, region, access_key, secret_key. Never print it.
Default is an offline inventory; --upload performs writes to demo/v1/ only.
"""

import argparse
import hashlib
import json
import mimetypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inventory():
    result = []
    for group, file in [
        ("police", "security"),
        ("nursing", "hospital"),
        ("memory", "memory"),
    ]:
        # Keep the complete synthetic bundle in each isolated scenario prefix so
        # references remain resolvable, including shared employee portraits.
        paths = [ROOT / "simulator/workspaces" / (file + ".json")]
        paths += sorted((ROOT / "simulator/workspaces/assets").iterdir())
        for path in paths:
            if path.is_file() and path.suffix.lower() in {
                ".json",
                ".png",
                ".jpg",
                ".mp4",
            }:
                result.append((path, f"demo/v1/{group}/{path.name}"))
    for path in sorted((ROOT / "simulator/acceptance").glob("*.pdf")):
        result.append((path, f"demo/v1/qa/{path.name}"))
    for name in [
        "alex-rivera.png",
        "maya-johnson.png",
        "evidence-desk.png",
        "evidence-desk-1.mp4",
    ]:
        result.append(
            (ROOT / "simulator/workspaces/assets" / name, "demo/v1/qa/" + name)
        )
    directory = ROOT / "simulator/social-directory"
    for folder in ("source", "muse", "generated", "workshop"):
        for path in sorted((directory / folder).rglob("*")):
            if path.is_file() and path.suffix.lower() in {
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
                ".mp4",
            }:
                result.append(
                    (
                        path,
                        "demo/v1/social-directory/"
                        + path.relative_to(directory).as_posix(),
                    )
                )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials-file", type=Path)
    parser.add_argument("--upload", action="store_true")
    parser.add_argument("--create-bucket", action="store_true")
    parser.add_argument(
        "--manifest", type=Path, default=ROOT / ".runtime/bucket-demo-manifest.json"
    )
    args = parser.parse_args()
    client = None
    bucket = None
    if args.upload:
        import boto3
        from app.storage.client import endpoint_address
        from botocore.config import Config

        if not args.credentials_file:
            parser.error("--upload requires a private --credentials-file")
        config = json.loads(args.credentials_file.read_text())
        endpoint_address(config["endpoint"])
        bucket = config["bucket"]
        client = boto3.client(
            "s3",
            endpoint_url=config["endpoint"],
            region_name=config.get("region", "auto"),
            aws_access_key_id=config["access_key"],
            aws_secret_access_key=config["secret_key"],
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )
        if args.create_bucket:
            client.create_bucket(Bucket=bucket)
    manifest = []
    for path, key in inventory():
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if client:
            client.put_object(
                Bucket=bucket,
                Key=key,
                Body=raw,
                ContentType=mimetypes.guess_type(path.name)[0]
                or "application/octet-stream",
                Metadata={"sha256": digest, "synthetic": "true"},
            )
            reply = client.get_object(Bucket=bucket, Key=key)
            with reply["Body"] as body:
                downloaded = body.read()
            if hashlib.sha256(downloaded).hexdigest() != digest:
                raise RuntimeError("R2 read-back checksum mismatch")
        manifest.append(
            {
                "source": str(path.relative_to(ROOT)),
                "key": key,
                "sha256": digest,
                "bytes": len(raw),
                "remote_verified": bool(client),
            }
        )
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps({"uploaded": bool(client), "items": manifest}, indent=2) + "\n"
    )
    args.manifest.chmod(0o600)
    print(
        f"{len(manifest)} synthetic resources {'uploaded and verified' if client else 'inventoried offline'}; manifest: {args.manifest}"
    )


if __name__ == "__main__":
    main()
