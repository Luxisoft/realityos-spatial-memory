"""Generate 10 genuinely different photos per directory profile with Muse Image.

Each profile keeps its source portrait (``simulator/social-directory/source``)
only as an identity anchor. One Muse conversation per profile produces a
neutral anchor turn plus 10 forked scene turns, all validated with the
production InsightFace engine before they can be imported.

Refuses to run unless ``META_MODE=live`` and ``muse-image-1.0`` is listed by
``GET /v1/models``. Resumable through per-profile manifests.

Run inside the ``api`` container (it holds the gateway token, InsightFace and
PIL), with the portraits copied in and the output copied back to
``simulator/social-directory/muse/``.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _extra in (ROOT / "backend", ROOT / "scripts"):
    if _extra.is_dir() and str(_extra) not in sys.path:
        sys.path.append(str(_extra))

import httpx  # noqa: E402
from PIL import Image  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.faces import build_face_engine, cosine_similarity  # noqa: E402
from seed_social_directory import PROFILE_ROWS  # noqa: E402

MODEL = "muse-image-1.0"
SCENES = (
    "trabajo",
    "calle",
    "hogar",
    "deporte",
    "cafe",
    "viaje",
    "formal",
    "selfie",
    "trayecto",
    "findesemana",
)
MAX_CALLS = 390
RETRIES_PER_SCENE = 1
MIN_SIBLING_DHASH_DISTANCE = 10
REQUEST_TIMEOUT_SECONDS = 300
REFERENCE_MAX_DIM = 768

IDENTITY_PREFIX = (
    "Photorealistic candid amateur photo of the same person from the {anchor}: "
    "identical face, same age, same facial features, skin tone, hair color and "
    "hair length, same distinctive marks such as tattoos, piercings, moles or "
    "freckles. "
)
SCENE_SUFFIX = (
    " Exactly one person clearly visible, face unobstructed and in focus. "
    "Natural imperfections, subtle grain, authentic snapshot feel, no watermark, "
    "no text, no logos."
)

# Deterministic variation pools, indexed by (profile_index, scene_index) so no
# profile repeats a background/clothing combination.
CASUAL_TOPS = (
    "a white linen shirt",
    "a mustard knit sweater",
    "a striped navy t-shirt",
    "a denim jacket over a gray tee",
    "a green oversized hoodie",
    "an ochre short-sleeve shirt",
    "a black turtleneck",
    "a floral summer blouse",
    "a rust-colored cardigan",
    "a light blue chambray shirt",
)
CASUAL_BOTTOMS = (
    "denim shorts",
    "dark jeans",
    "khaki chinos",
    "a black midi skirt",
    "olive cargo pants",
    "white wide-leg trousers",
    "plaid shorts",
    "gray sweatpants",
    "a pleated beige skirt",
    "faded straight jeans",
)
LIGHTING = (
    "bright morning daylight",
    "soft overcast daylight",
    "warm golden-hour light",
    "harsh midday sun with strong shadows",
    "cool blue-hour tones",
    "warm indoor tungsten light",
    "diffused window light",
    "neon-tinted night light",
    "dappled shade under trees",
    "pale rainy-day light",
)
FRAMING = (
    "vertical portrait orientation, waist-up framing",
    "square format, three-quarter framing",
    "wide landscape orientation, full-body framing",
    "vertical portrait orientation, close-up framing",
    "square format, waist-up framing",
    "wide landscape orientation, environmental framing",
    "vertical portrait orientation, full-body framing",
    "square format, close-up framing",
    "wide landscape orientation, waist-up framing",
    "vertical portrait orientation, three-quarter framing",
)
LEISURE = (
    "flying a kite in a large urban park",
    "browsing vinyl records at a flea market",
    "painting a small canvas outdoors",
    "playing with a friendly stray dog",
    "reading a paperback on a plaza bench",
    "riding a bicycle along a riverside path",
    "tending a small community garden plot",
    "playing an acoustic guitar with friends nearby",
    "sketching street life in a notebook",
    "sharing a picnic with friends on the grass",
)
TRAVEL = (
    "a colonial old-town square with a stone church",
    "a dramatic coastal cliff viewpoint",
    "a colorful street-food market",
    "a misty mountain lookout",
    "a botanical garden greenhouse",
    "a historic fortress courtyard",
    "a lakeside boardwalk at dusk",
    "a desert dune ridge",
    "a waterfall trail in a cloud forest",
    "a rooftop terrace overlooking the city",
)
COMMUTE = (
    "waiting on a sunlit bus-stop bench",
    "standing inside a modern metro car",
    "cycling through a quiet residential street",
    "walking across a pedestrian bridge at rush hour",
    "sitting by the window of a city bus",
    "riding a motorcycle taxi through traffic",
    "waiting on a train platform",
    "crossing a zebra crossing downtown",
    "sitting in a yellow taxi back seat",
    "walking up subway stairs with commuters behind",
)
SPORT = (
    "jogging in a park wearing athletic gear",
    "doing yoga stretches on a rooftop mat",
    "playing casual weekend football on a dirt pitch",
    "swimming laps in a public pool",
    "lifting light weights at a neighborhood gym",
    "dancing in an open-air fitness class",
    "hiking an uphill trail with a backpack",
    "stretching before a morning run on the track",
    "playing basketball on an outdoor court",
    "cycling uphill on a mountain road",
)
WORK_SETTINGS = (
    ("modern office desk with dual monitors", "a blazer over a plain shirt"),
    ("field site with tools and equipment", "a work vest and boots"),
    ("creative studio with sketches pinned up", "an apron over casual clothes"),
    ("consulting room with bookshelves", "a formal shirt and trousers"),
    ("workshop bench with ongoing craft work", "rolled sleeves and gloves nearby"),
    ("outdoor survey location with instruments", "a cap and field jacket"),
    ("classroom with whiteboard and students' desks", "a smart casual outfit"),
    ("laboratory bench with samples", "a lab coat over dark clothes"),
    ("market stall running a small business", "a branded polo shirt"),
    ("construction or renovation site", "a helmet and reflective vest"),
)
HOME_SETTINGS = (
    "a cozy living room with plants and a sofa",
    "a small kitchen while cooking",
    "a bedroom reading nook by the window",
    "a home office desk with a laptop",
    "a balcony with city views and hanging plants",
    "a dining table set for one",
    "a laundry room folding clothes",
    "a hallway with framed photos",
    "a study corner full of books",
    "a terrace hammock",
)
CAFE_SETTINGS = (
    "a cozy neighborhood cafe with a cortado coffee",
    "a bakery counter holding a paper bag of bread",
    "an ice-cream parlor with a sundae glass",
    "a rooftop bar with a lemonade at sunset",
    "a traditional market fonda with a lunch tray",
    "a modern brunch spot with avocado toast",
    "a street coffee cart holding a paper cup",
    "a quiet tea house with a ceramic teapot",
    "a pizzeria table with a slice on a plate",
    "a juice stand with a fresh orange juice",
)
FORMAL_SETTINGS = (
    "an evening wedding reception in elegant attire",
    "a graduation-style ceremony in formal wear",
    "a gallery opening in a tailored outfit",
    "a theater lobby before the show, dressed up",
    "a rooftop wedding toast at night, elegant dress",
    "a conference gala dinner in a suit",
    "a classical concert hall foyer, formal outfit",
    "an awards-style event with a step-and-repeat wall",
    "a candlelit anniversary dinner, refined attire",
    "a museum benefit night in evening wear",
)


def scene_body(
    profile_index: int,
    scene_index: int,
    profession: str,
    region: str,
    retry_variant: int = 0,
) -> tuple[str, str]:
    """Return (scene_name, body) deterministically varied per profile/scene."""

    scene = SCENES[scene_index]
    top = CASUAL_TOPS[(profile_index * 3 + scene_index * 7 + retry_variant) % len(CASUAL_TOPS)]
    bottom = CASUAL_BOTTOMS[
        (profile_index * 5 + scene_index * 3 + retry_variant * 2) % len(CASUAL_BOTTOMS)
    ]
    light = LIGHTING[(profile_index + scene_index * 2 + retry_variant) % len(LIGHTING)]
    framing = FRAMING[(scene_index + retry_variant) % len(FRAMING)]
    work_setting, work_attire = WORK_SETTINGS[
        (profile_index + scene_index + retry_variant) % len(WORK_SETTINGS)
    ]

    if scene == "trabajo":
        body = (
            f"They are a {profession} at work in {work_setting} in {region}, "
            f"wearing {work_attire}, captured mid-task."
        )
    elif scene == "calle":
        body = (
            f"They are walking on a lively street in {region}, wearing {top} and "
            f"{bottom}, candid mid-stride moment."
        )
    elif scene == "hogar":
        home = HOME_SETTINGS[(profile_index * 2 + scene_index + retry_variant) % len(HOME_SETTINGS)]
        body = (
            f"They are relaxing at home in {home}, wearing comfortable home "
            f"clothes ({top} and {bottom}), unposed moment."
        )
    elif scene == "deporte":
        sport = SPORT[(profile_index * 4 + scene_index + retry_variant) % len(SPORT)]
        body = f"They are {sport}, {light}."
    elif scene == "cafe":
        cafe = CAFE_SETTINGS[(profile_index + scene_index * 3 + retry_variant) % len(CAFE_SETTINGS)]
        body = (
            f"They are sitting in {cafe}, wearing {top} and {bottom}, "
            "genuine relaxed expression."
        )
    elif scene == "viaje":
        trip = TRAVEL[(profile_index * 7 + scene_index + retry_variant) % len(TRAVEL)]
        body = (
            f"They are traveling, posing naturally at {trip} near {region}, "
            f"wearing {top}, {bottom} and comfortable shoes, tourist snapshot."
        )
    elif scene == "formal":
        formal = FORMAL_SETTINGS[
            (profile_index * 3 + scene_index + retry_variant) % len(FORMAL_SETTINGS)
        ]
        body = f"They are attending {formal}, polished but natural look."
    elif scene == "selfie":
        body = (
            f"Smartphone selfie taken by themself on an everyday street in {region}, "
            f"wearing {top}, slight arm-extended perspective, casual background detail."
        )
    elif scene == "trayecto":
        commute = COMMUTE[
            (profile_index * 5 + scene_index * 2 + retry_variant) % len(COMMUTE)
        ]
        body = (
            f"They are commuting, {commute}, wearing {top} and {bottom}, "
            "candid unposed moment."
        )
    else:
        leisure = LEISURE[
            (profile_index * 2 + scene_index * 5 + retry_variant) % len(LEISURE)
        ]
        body = (
            f"Weekend leisure: they are {leisure}, wearing {top} and {bottom}."
        )
    if retry_variant:
        body += " Choose a clearly different framing and background arrangement."
    return scene, (
        body + f" {framing}, {light}." if scene != "deporte" else body + f" {framing}."
    )


def scene_prompt(
    profile_index: int,
    scene_index: int,
    profession: str,
    region: str,
    *,
    anchor: str,
    retry_variant: int = 0,
) -> tuple[str, str]:
    """Return (scene_name, prompt) deterministically varied per profile/scene."""

    scene, body = scene_body(
        profile_index, scene_index, profession, region, retry_variant
    )
    prompt = IDENTITY_PREFIX.format(anchor=anchor) + body + SCENE_SUFFIX
    return scene, prompt


def dhash(image_bytes: bytes) -> int:
    with Image.open(io.BytesIO(image_bytes)) as picture:
        gray = picture.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
        pixels = list(gray.getdata())
    digest = 0
    for row in range(8):
        for col in range(8):
            if pixels[row * 9 + col] > pixels[row * 9 + col + 1]:
                digest |= 1 << (row * 8 + col)
    return digest


def hamming(left: int, right: int) -> int:
    return bin(left ^ right).count("1")


class CallBudget:
    def __init__(self, path: Path, limit: int = MAX_CALLS) -> None:
        self.path = path
        self.limit = limit
        self.used = 0
        if path.exists():
            try:
                self.used = int(json.loads(path.read_text()).get("total_calls", 0))
            except (ValueError, TypeError, KeyError):
                self.used = 0

    def spend(self) -> None:
        if self.used >= self.limit:
            raise RuntimeError(f"Muse call budget exhausted ({self.limit}).")
        self.used += 1
        self.path.write_text(json.dumps({"total_calls": self.used}))


class MuseImage:
    def __init__(self) -> None:
        settings = get_settings()
        if settings.meta_mode != "live":
            raise RuntimeError("Refusing to generate: META_MODE is not 'live'.")
        if settings.meta_gateway_base_url:
            if not settings.meta_gateway_token:
                raise RuntimeError("Refusing to generate: META_GATEWAY_TOKEN is missing.")
            self.base_url = str(settings.meta_gateway_base_url).rstrip("/")
            self.headers = {"X-RealityOS-Gateway-Token": settings.meta_gateway_token}
        else:
            if not settings.model_api_key:
                raise RuntimeError("Refusing to generate: MODEL_API_KEY is missing.")
            self.base_url = "https://api.meta.ai/v1"
            self.headers = {"Authorization": f"Bearer {settings.model_api_key}"}
        self.settings = settings
        models = httpx.get(
            f"{self.base_url}/models", headers=self.headers, timeout=30
        )
        models.raise_for_status()
        ids = {item.get("id") for item in models.json().get("data", [])}
        if MODEL not in ids:
            raise RuntimeError(f"Refusing to generate: {MODEL} is not in /v1/models.")

    def create(self, payload: dict) -> dict:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = httpx.post(
                    f"{self.base_url}/responses",
                    headers=self.headers,
                    json=payload,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                if response.status_code in {408, 429, 500, 502, 503, 504}:
                    last_error = RuntimeError(f"upstream {response.status_code}")
                else:
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPError as exc:
                last_error = exc
            time.sleep(2.0 * (2**attempt))
        raise RuntimeError(f"Muse request failed: {last_error}")

    @staticmethod
    def extract_image(payload: dict) -> tuple[str, bytes, dict]:
        response_id = str(payload.get("id") or "")
        if payload.get("status") != "completed" or not response_id:
            raise RuntimeError("Muse response did not complete.")
        for item in payload.get("output", []):
            if item.get("type") == "image_generation_call":
                if item.get("status") != "completed" or not item.get("result"):
                    raise RuntimeError("Image generation call did not complete.")
                return (
                    response_id,
                    base64.b64decode(item["result"]),
                    payload.get("usage") or {},
                )
        raise RuntimeError("Muse response carried no image.")


def reference_data_url(source: Path) -> str:
    with Image.open(source) as original:
        rgb = original.convert("RGB")
        rgb.thumbnail((REFERENCE_MAX_DIM, REFERENCE_MAX_DIM), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        rgb.save(output, format="JPEG", quality=85, optimize=True)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def contact_sheet(directory: Path, slug: str) -> None:
    thumbs: list[Image.Image] = []
    for index in range(10):
        path = directory / f"photo-{index + 1:02d}.jpg"
        with Image.open(path) as picture:
            thumbs.append(picture.convert("RGB").resize((256, 320), Image.Resampling.LANCZOS))
    sheet = Image.new("RGB", (256 * 5, 320 * 2), "white")
    for position, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((position % 5) * 256, (position // 5) * 320))
    sheet.save(directory / "contact-sheet.jpg", quality=85, optimize=True)
    print(f"[{slug}] contact sheet ready")


def generate_profile(
    client: MuseImage,
    engine,
    threshold: float,
    profile_index: int,
    row: tuple,
    source_root: Path,
    output_root: Path,
    budget: CallBudget,
    known_hashes: set[str],
) -> None:
    slug, _name, profession, region, _gender, _tags = row
    source = source_root / f"{slug}.png"
    if not source.exists():
        raise FileNotFoundError(f"Missing source portrait: {source}")
    directory = output_root / slug
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = directory / "manifest.json"
    manifest: dict = (
        json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    )
    scenes = manifest.setdefault("scenes", {})

    with Image.open(source) as portrait:
        portrait.convert("RGB").save(directory / "anchor-source.jpg", quality=90)
    anchor_faces = engine.detect_faces(source.read_bytes())
    if not anchor_faces:
        raise RuntimeError(f"[{slug}] no face detected in the source portrait.")
    anchor_face = max(anchor_faces, key=lambda face: face.quality)
    print(f"[{slug}] anchor faces={len(anchor_faces)}")

    anchor_response_id = manifest.get("anchor_response_id")
    if not anchor_response_id or not (directory / "anchor.jpg").exists():
        budget.spend()
        payload = {
            "model": MODEL,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                IDENTITY_PREFIX.format(anchor="reference portrait")
                                + "They are standing against a plain neutral "
                                "studio backdrop, wearing a simple gray "
                                "t-shirt, soft even lighting, facing the "
                                "camera. This portrait fixes their identity "
                                "for the series."
                                + SCENE_SUFFIX
                            ),
                        },
                        {
                            "type": "input_image",
                            "image_url": reference_data_url(source),
                        },
                    ],
                }
            ],
        }
        response_id, raw, usage = MuseImage.extract_image(client.create(payload))
        (directory / "anchor.jpg").write_bytes(raw)
        anchor_response_id = response_id
        manifest["anchor_response_id"] = response_id
        manifest["anchor_usage"] = usage
        manifest["anchor_faces"] = len(anchor_faces)
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print(f"[{slug}] anchor ready ({response_id})")
        time.sleep(2)
    else:
        print(f"[{slug}] reusing anchor {anchor_response_id}")

    sibling_hashes = {
        entry["dhash"]
        for entry in scenes.values()
        if entry.get("status") == "done" and isinstance(entry.get("dhash"), int)
    }
    for scene_index in range(10):
        key = f"photo-{scene_index + 1:02d}"
        entry = scenes.get(key, {})
        if entry.get("status") == "done" and (directory / f"{key}.jpg").exists():
            known_hashes.add(entry["sha256"])
            continue
        scene_name, _ = scene_prompt(
            profile_index, scene_index, profession, region, anchor="previous image"
        )
        attempts = int(entry.get("attempts", 0))
        while attempts <= RETRIES_PER_SCENE:
            _scene, prompt = scene_prompt(
                profile_index,
                scene_index,
                profession,
                region,
                anchor="previous image",
                retry_variant=attempts,
            )
            budget.spend()
            attempts += 1
            try:
                payload = {
                    "model": MODEL,
                    "previous_response_id": anchor_response_id,
                    "input": prompt,
                }
                response_id, raw, usage = MuseImage.extract_image(client.create(payload))
                with Image.open(io.BytesIO(raw)) as picture:
                    width, height = picture.size
                    picture.load()
                with Image.open(io.BytesIO(raw)) as picture:
                    picture.verify()
                digest = hashlib.sha256(raw).hexdigest()
                if digest in known_hashes:
                    raise RuntimeError("duplicate bytes already generated.")
                faces = engine.detect_faces(raw)
                if len(faces) != 1:
                    raise RuntimeError(f"expected 1 face, detected {len(faces)}.")
                similarity = cosine_similarity(anchor_face.embedding, faces[0].embedding)
                if similarity < threshold:
                    raise RuntimeError(f"identity drift (similarity {similarity:.3f}).")
                digest_dhash = dhash(raw)
                nearest = (
                    min(hamming(digest_dhash, other) for other in sibling_hashes)
                    if sibling_hashes
                    else 64
                )
                if nearest < MIN_SIBLING_DHASH_DISTANCE:
                    raise RuntimeError(
                        f"too similar to a sibling scene (dhash {nearest})."
                    )
            except Exception as exc:
                print(f"[{slug}] {key} attempt {attempts} rejected: {exc}")
                time.sleep(2)
                continue
            (directory / f"{key}.jpg").write_bytes(raw)
            known_hashes.add(digest)
            sibling_hashes.add(digest_dhash)
            scenes[key] = {
                "scene": scene_name,
                "response_id": response_id,
                "prompt": prompt,
                "sha256": digest,
                "bytes": len(raw),
                "width": width,
                "height": height,
                "faces": 1,
                "similarity": round(similarity, 4),
                "dhash": digest_dhash,
                "usage": usage,
                "attempts": attempts,
                "status": "done",
                "generated_at": datetime.now(UTC).isoformat(),
            }
            manifest_path.write_text(json.dumps(manifest, indent=2))
            print(
                f"[{slug}] {key} done sim={similarity:.3f} "
                f"dhash_min={nearest} attempts={attempts}"
            )
            time.sleep(2)
            break
        else:
            scenes[key] = {"scene": scene_name, "attempts": attempts, "status": "failed"}
            manifest_path.write_text(json.dumps(manifest, indent=2))
            raise RuntimeError(f"[{slug}] {key} failed after {attempts} attempts.")
    contact_sheet(directory, slug)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", default=str(ROOT / "simulator/social-directory/source"))
    parser.add_argument("--output-root", default=str(ROOT / "simulator/social-directory/muse"))
    parser.add_argument("--slugs", default="", help="Comma-separated subset to generate.")
    parser.add_argument("--max-calls", type=int, default=MAX_CALLS)
    args = parser.parse_args()
    source_root = Path(args.source_root)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    wanted = {slug.strip() for slug in args.slugs.split(",") if slug.strip()}
    rows = [
        (index, row)
        for index, row in enumerate(PROFILE_ROWS)
        if not wanted or row[0] in wanted
    ]
    if not rows:
        raise SystemExit("No profiles selected.")
    client = MuseImage()
    settings = client.settings
    engine = build_face_engine(settings)
    if engine.simulated:
        raise RuntimeError("Refusing to generate: face engine is simulated.")
    threshold = settings.face_match_threshold
    print(f"engine={engine.name} threshold={threshold} profiles={len(rows)}")

    budget = CallBudget(output_root / "calls.json", limit=args.max_calls)
    known_hashes: set[str] = set()
    for slug_dir in output_root.iterdir():
        manifest_path = slug_dir / "manifest.json"
        if not manifest_path.is_file():
            continue
        try:
            scenes = json.loads(manifest_path.read_text()).get("scenes", {})
        except ValueError:
            continue
        for entry in scenes.values():
            if entry.get("status") == "done" and entry.get("sha256"):
                known_hashes.add(entry["sha256"])
    print(f"resuming with {len(known_hashes)} known photos, {budget.used} calls spent")

    for profile_index, row in rows:
        generate_profile(
            client,
            engine,
            threshold,
            profile_index,
            row,
            source_root,
            output_root,
            budget,
            known_hashes,
        )
    print(f"done: {budget.used} Muse calls spent")


if __name__ == "__main__":
    main()
