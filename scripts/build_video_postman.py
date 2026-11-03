"""Executable evidence checks for the reviewed, licensed video scenarios."""

import copy
import json


def video_requests(template, videos):
    items = []
    for video in videos:
        for number, query in enumerate(video["queries"], 1):
            for language in ("es", "en"):
                item = copy.deepcopy(template)
                item["name"] = f"Video {video['id']} · {number} · {language.upper()}"
                item["response"] = []
                item["request"]["body"]["raw"] = json.dumps(
                    {
                        "workspace_id": "{{workspace_id}}",
                        "search_scope": "gallery",
                        "question": query[language],
                        "language": language,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                start, end = query["visible_ms"]
                item["request"]["description"] = (
                    f"{query[language]} Expected recorded object: {query['target']}. "
                    f"Evidence must come from video {video['id']} between "
                    f"{start / 1000:g} and {end / 1000:g} seconds. "
                    "The account language preference, when set, controls the answer. "
                    "Gallery matches are valid even when the Register-only found field is false. "
                    "Open boxed_url to inspect the object and media_url for the original. "
                    "Last seen describes recorded evidence, not the object's current location."
                )
                tests = next(
                    event["script"]["exec"]
                    for event in item["event"]
                    if event["listen"] == "test"
                )
                tests.extend(
                    [
                        f"const expectedPost = {json.dumps(video['post_id'])};",
                        "const videoEvidence = (pm.response.json().gallery_matches || []).find(m => m.post_id === expectedPost);",
                        'pm.test("Reviewed video is retrieved", () => pm.expect(videoEvidence).to.be.an("object"));',
                        "if (videoEvidence) {",
                        f'  pm.test("Frame is inside the observed interval", () => pm.expect(videoEvidence.frame_timestamp_ms).to.be.within({start}, {end}));',
                        '  pm.test("Real SAM video evidence", () => { pm.expect(videoEvidence.simulated).to.eql(false); pm.expect(videoEvidence.localization_quality).to.eql("sam"); pm.expect(videoEvidence.mime_type).to.eql("video/mp4"); pm.expect(videoEvidence.boxed_url).to.be.a("string").and.not.empty; });',
                        "}",
                    ]
                )
                items.append(item)
    return items
