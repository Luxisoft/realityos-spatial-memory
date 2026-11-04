"""Pure normalized image geometry shared by processing and providers."""

import math


def valid_box(box) -> dict | None:
    try:
        x, y, w, h = (float(box[k]) for k in ("x", "y", "width", "height"))
        if not all(math.isfinite(v) for v in (x, y, w, h)) or w <= 0 or h <= 0:
            return None
        left, top, right, bottom = max(0.0, x), max(0.0, y), min(1.0, x + w), min(1.0, y + h)
        if right <= left or bottom <= top:
            return None
        return dict(x=left, y=top, width=right - left, height=bottom - top)
    except (KeyError, TypeError, ValueError):
        return None


def overlap(a, b):
    area = max(0, min(a["x"] + a["width"], b["x"] + b["width"]) - max(a["x"], b["x"])) * max(
        0, min(a["y"] + a["height"], b["y"] + b["height"]) - max(a["y"], b["y"])
    )
    return area / (a["width"] * a["height"] + b["width"] * b["height"] - area) if area else 0.0
