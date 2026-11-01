"""Small Display callouts that never paint a filled badge over a face."""

from PIL import Image, ImageDraw, ImageFont, ImageOps

CARD_SIZE = (600, 280)
PHOTO_HEIGHT = 256


def _overlaps(first, second):
    return (
        first[0] < second[2]
        and second[0] < first[2]
        and first[1] < second[3]
        and second[1] < first[3]
    )


def render_face_group(frame, marks):
    picture = ImageOps.contain(frame.convert("RGB"), (CARD_SIZE[0], PHOTO_HEIGHT))
    canvas = Image.new("RGB", CARD_SIZE, "black")
    offset_x = (CARD_SIZE[0] - picture.width) // 2
    offset_y = (PHOTO_HEIGHT - picture.height) // 2
    canvas.paste(picture, (offset_x, offset_y))
    boxes = []
    for mark in marks:
        left = offset_x + min(picture.width - 1, round(mark.box["x"] * picture.width))
        top = offset_y + min(picture.height - 1, round(mark.box["y"] * picture.height))
        right = min(
            offset_x + picture.width - 1,
            max(left + 1, round(left + mark.box["width"] * picture.width)),
        )
        bottom = min(
            offset_y + picture.height - 1,
            max(top + 1, round(top + mark.box["height"] * picture.height)),
        )
        boxes.append((left, top, right, bottom))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=12)
    occupied = []
    # All face boxes are obstacles, including faces whose badge is drawn later.
    obstacles = [(left - 2, top - 2, right + 2, bottom + 2) for left, top, right, bottom in boxes]
    for index, (mark, box) in enumerate(zip(marks, boxes, strict=True)):
        rgb = tuple(int(mark.color[start : start + 2], 16) for start in (1, 3, 5))
        left, top, right, bottom = box
        stroke = 1 if min(right - left, bottom - top) < 24 else 2
        draw.rectangle(
            (
                max(0, left - stroke),
                max(0, top - stroke),
                min(599, right + stroke),
                min(PHOTO_HEIGHT - 1, bottom + stroke),
            ),
            outline=rgb,
            width=stroke,
        )
        text = str(mark.number)
        text_box = draw.textbbox((0, 0), text, font=font)
        width = max(18, text_box[2] - text_box[0] + 8)
        height = max(18, text_box[3] - text_box[1] + 8)
        candidates = [
            (left, top - height - 4),
            (right + 4, top),
            (left, bottom + 4),
            (left - width - 4, top),
        ]
        badge = None
        for x, y in candidates:
            proposed = (x, y, x + width, y + height)
            if x < 0 or y < 0 or x + width >= CARD_SIZE[0] or y + height >= PHOTO_HEIGHT:
                continue
            if not any(_overlaps(proposed, obstacle) for obstacle in obstacles + occupied):
                badge = proposed
                break
        if badge is None:
            # Twenty 28px slots fit below the photograph. Even a full-frame
            # face or a crowded group therefore keeps every filled label out.
            x = 4 + index * 28
            badge = (x, PHOTO_HEIGHT + 3, x + width, PHOTO_HEIGHT + 3 + height)
        occupied.append(badge)
        draw.rounded_rectangle(badge, radius=3, fill=rgb)
        ink = (
            "black"
            if sum(value * weight for value, weight in zip(rgb, (0.299, 0.587, 0.114), strict=True))
            > 140
            else "white"
        )
        draw.text(
            (badge[0] + 4 - text_box[0], badge[1] + 4 - text_box[1]), text, fill=ink, font=font
        )
    return canvas
