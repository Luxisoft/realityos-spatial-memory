"""Request examples for runtime requirements not expressed by OpenAPI required fields."""

JSON_EXAMPLES = {
    "POST /v1/gallery": {
        "media_id": "{{media_id}}",
        "audience": "work",
        "workspace_id": "{{workspace_id}}",
    },
    "POST /v1/gallery/{post_id}/share": {
        "audience": "work",
        "workspace_id": "{{workspace_id}}",
    },
    "POST /v1/groups/{workspace_id}/publications/import": {
        "publication_ids": ["{{post_id}}"],
    },
    "POST /v1/groups": {"name": "New work group"},
    "POST /v1/groups/join": {"code": "{{invite_code}}"},
    "POST /v1/groups/{workspace_id}/members/{member_id}/invite-permission": {
        "allowed": False,
    },
    "PATCH /v1/me/profile": {"display_name": "{{display_name}}"},
}

GROUP_DESTINATION = (
    "Choose an existing work group in workspace_id; membership is required. "
    "Publications cannot use a private or public destination."
)

REQUEST_NOTES = {
    "POST /v1/gallery": GROUP_DESTINATION,
    "POST /v1/gallery/{post_id}/share": GROUP_DESTINATION,
    "POST /v1/groups/{workspace_id}/publications/import": (
        GROUP_DESTINATION + " Supply 1–100 IDs of publications owned by this account."
    ),
    "POST /v1/me/publication-uploads": (
        GROUP_DESTINATION
        + " Select file as a file, not text. Use a new request_key for each new upload; "
        "reuse it only when retrying the same attempt. Poll GET /v1/me/publication-uploads/"
        "{upload_id} after 202. Confirm or cancel a duplicate using its returned upload ID."
    ),
    "POST /v1/groups/join": (
        "Set invite_code to the code returned by POST /v1/groups/{workspace_id}/invite. "
        "For a numeric group PIN, use POST /v1/groups/join-by-pin instead."
    ),
    "POST /v1/faces/consent": (
        "Read GET /v1/faces/consent first. Set confirm=true only after the account holder "
        "accepts biometric enrollment. The example does not grant consent automatically."
    ),
    "POST /v1/faces/profile-photo": (
        "After consent, select one clear portrait as file. This registers the recognition "
        "identity; POST /v1/me/profile/avatar separately sets the visible profile picture."
    ),
    "POST /v1/me/profile/avatar": (
        "Select the visible profile picture as file (JPEG, PNG or WebP). "
        "The API normalizes EXIF orientation. This upload does not enroll a reference face."
    ),
    "POST /v1/faces/reference-photos": (
        "After consent and the recognition profile photo, send one distinct image per request "
        "as file. Each must contain exactly one face matching that profile. Accepted references "
        "remain private; they are not publications. GET /v1/faces/setup reports accepted_photos "
        "and reference_ids. Repeated files do not increase the count; read detail on a 422."
    ),
    "POST /v1/faces/setup/complete": (
        "Requires consent, a recognition profile photo, a visible avatar and 3–25 distinct "
        "accepted references. Check GET /v1/faces/setup before and after completion."
    ),
    "POST /v1/faces/search": (
        "Select probe as a file. To search an existing authorized media asset instead, "
        "disable probe and enable media_id. Consent and workspace membership are required."
    ),
}


def customize_form(name, fields):
    for field in fields:
        if name == "POST /v1/me/publication-uploads" and field["key"] in {
            "workspace_id",
            "audience",
        }:
            field["disabled"] = False
        if name == "POST /v1/faces/search" and field["key"] == "probe":
            field["disabled"] = False
