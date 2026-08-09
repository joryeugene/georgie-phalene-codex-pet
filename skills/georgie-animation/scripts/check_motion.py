#!/usr/bin/env python3
"""Fail when a Georgie v2 atlas contains structural motion drift."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageFilter


CELL_W = 192
CELL_H = 208
NEUTRAL_HEIGHT_RANGE = (142, 148)
GROUNDED_BASELINE_RANGE = (200, 204)
FRAME_COUNTS = (6, 8, 8, 4, 5, 8, 6, 6, 6, 8, 8)
STATE_NAMES = (
    "idle",
    "running-right",
    "running-left",
    "waving",
    "jumping",
    "failed",
    "waiting",
    "running",
    "review",
    "look-a",
    "look-b",
)

SUBTLE_LIMITS = {
    "idle": (4, 2, 2.0, 2.0, 2.0, 0.88),
    "waving": (5, 2, 2.0, 2.0, 2.0, 0.82),
    "waiting": (4, 2, 2.0, 2.0, 2.0, 0.88),
    "running": (5, 1, 1.0, 0.8, 1.5, 0.90),
    "review": (3, 1, 0.5, 0.5, 1.0, 0.92),
    "look-a": (5, 2, 2.0, 3.5, 2.5, 0.72),
    "look-b": (5, 2, 2.0, 3.5, 2.5, 0.72),
}

GROUNDED_STATES = {"idle", "waving", "waiting", "running", "review", "look-a", "look-b"}
RUNNING_CORE_BOX = (30, 50, 110, 204)
RUNNING_CORE_PIXEL_CHANGE_LIMIT = 0.06
RUNNING_CORE_ALPHA_CHANGE_LIMIT = 0.02


def alpha_bbox(frame: Image.Image) -> tuple[int, int, int, int] | None:
    return frame.getchannel("A").point(lambda value: 255 if value > 16 else 0).getbbox()


def anchor_center(frame: Image.Image) -> float | None:
    alpha = frame.getchannel("A")
    box = alpha_bbox(frame)
    if box is None:
        return None
    start_y = box[1] + round((box[3] - box[1]) * 0.45)
    stop_y = box[1] + round((box[3] - box[1]) * 0.80)
    xs: list[int] = []
    for y in range(start_y, stop_y):
        for x in range(CELL_W):
            if alpha.getpixel((x, y)) > 16:
                xs.append(x)
    return sum(xs) / len(xs) if xs else None


def head_center(frame: Image.Image) -> float | None:
    alpha = frame.getchannel("A")
    box = alpha_bbox(frame)
    if box is None:
        return None
    stop_y = box[1] + round((box[3] - box[1]) * 0.45)
    xs = [
        x
        for y in range(box[1], stop_y)
        for x in range(CELL_W)
        if alpha.getpixel((x, y)) > 16
    ]
    return sum(xs) / len(xs) if xs else None


def alpha_center(frame: Image.Image) -> float | None:
    alpha = frame.getchannel("A")
    weighted_x = 0
    weight = 0
    for y in range(CELL_H):
        for x in range(CELL_W):
            value = alpha.getpixel((x, y))
            if value > 16:
                weighted_x += x * value
                weight += value
    return weighted_x / weight if weight else None


def silhouette_iou(first: Image.Image, last: Image.Image) -> float:
    a = first.getchannel("A").point(lambda value: 1 if value > 16 else 0)
    b = last.getchannel("A").point(lambda value: 1 if value > 16 else 0)
    av = a.tobytes()
    bv = b.tobytes()
    intersection = sum(1 for left, right in zip(av, bv) if left and right)
    union = sum(1 for left, right in zip(av, bv) if left or right)
    return intersection / union if union else 1.0


def core_change_ratios(frames: list[Image.Image]) -> tuple[float, float]:
    cropped = [frame.crop(RUNNING_CORE_BOX) for frame in frames]
    blurred = [frame.filter(ImageFilter.GaussianBlur(1.5)) for frame in cropped]
    silhouettes = [
        frame.getchannel("A")
        .point(lambda value: 255 if value > 16 else 0)
        .filter(ImageFilter.MaxFilter(3))
        .filter(ImageFilter.MinFilter(3))
        for frame in cropped
    ]
    pixel_ratios: list[float] = []
    alpha_ratios: list[float] = []
    for index, current in enumerate(blurred):
        following = blurred[(index + 1) % len(blurred)]
        visible = pixel_changes = 0
        for left, right in zip(current.get_flattened_data(), following.get_flattened_data()):
            if left[3] <= 16 and right[3] <= 16:
                continue
            visible += 1
            pixel_changes += max(abs(left[channel] - right[channel]) for channel in range(4)) > 24
        pixel_ratios.append(pixel_changes / visible if visible else 0.0)

        alpha = silhouettes[index].tobytes()
        following_alpha = silhouettes[(index + 1) % len(silhouettes)].tobytes()
        intersection = sum(1 for left, right in zip(alpha, following_alpha) if left and right)
        union = sum(1 for left, right in zip(alpha, following_alpha) if left or right)
        alpha_ratios.append(1 - intersection / union if union else 0.0)
    return max(pixel_ratios), max(alpha_ratios)


def inspect(path: Path) -> dict[str, object]:
    atlas = Image.open(path).convert("RGBA")
    errors: list[str] = []
    rows: list[dict[str, object]] = []
    if atlas.size != (CELL_W * 8, CELL_H * 11):
        errors.append(f"atlas is {atlas.width}x{atlas.height}; expected 1536x2288")

    for row, (state, count) in enumerate(zip(STATE_NAMES, FRAME_COUNTS)):
        frames = [
            atlas.crop((column * CELL_W, row * CELL_H, (column + 1) * CELL_W, (row + 1) * CELL_H))
            for column in range(count)
        ]
        boxes = [alpha_bbox(frame) for frame in frames]
        if any(box is None for box in boxes):
            errors.append(f"{state}: used frame is empty")
            continue
        typed_boxes = [box for box in boxes if box is not None]
        heights = [box[3] - box[1] for box in typed_boxes]
        bottoms = [box[3] for box in typed_boxes]
        centers = [anchor_center(frame) for frame in frames]
        head_centers = [head_center(frame) for frame in frames]
        alpha_centers = [alpha_center(frame) for frame in frames]
        iou = silhouette_iou(frames[0], frames[-1])
        row_result: dict[str, object] = {
            "state": state,
            "median_height": sorted(heights)[len(heights) // 2],
            "median_baseline": sorted(bottoms)[len(bottoms) // 2],
            "height_range": max(heights) - min(heights),
            "baseline_range": max(bottoms) - min(bottoms),
            "anchor_center_range": round(max(c for c in centers if c is not None) - min(c for c in centers if c is not None), 3),
            "head_center_range": round(max(c for c in head_centers if c is not None) - min(c for c in head_centers if c is not None), 3),
            "alpha_center_range": round(max(c for c in alpha_centers if c is not None) - min(c for c in alpha_centers if c is not None), 3),
            "loop_iou": round(iou, 4),
        }
        if state == "running":
            core_pixel_change, core_alpha_change = core_change_ratios(frames)
            row_result["core_pixel_change_ratio"] = round(core_pixel_change, 4)
            row_result["core_alpha_change_ratio"] = round(core_alpha_change, 4)
            if core_pixel_change > RUNNING_CORE_PIXEL_CHANGE_LIMIT:
                errors.append(
                    f"running: fixed body pixels change {core_pixel_change:.1%}; "
                    f"limit is {RUNNING_CORE_PIXEL_CHANGE_LIMIT:.1%}"
                )
            if core_alpha_change > RUNNING_CORE_ALPHA_CHANGE_LIMIT:
                errors.append(
                    f"running: fixed body silhouette changes {core_alpha_change:.1%}; "
                    f"limit is {RUNNING_CORE_ALPHA_CHANGE_LIMIT:.1%}"
                )
        rows.append(row_result)
        if state in SUBTLE_LIMITS:
            height_limit, baseline_limit, anchor_limit, head_limit, silhouette_limit, iou_limit = SUBTLE_LIMITS[state]
            if row_result["height_range"] > height_limit:
                errors.append(f"{state}: height drifts {row_result['height_range']} px; limit is {height_limit}")
            if row_result["baseline_range"] > baseline_limit:
                errors.append(f"{state}: baseline drifts {row_result['baseline_range']} px; limit is {baseline_limit}")
            if state != "running" and row_result["anchor_center_range"] > anchor_limit:
                errors.append(f"{state}: lower-body anchor drifts {row_result['anchor_center_range']} px; limit is {anchor_limit}")
            if state != "running" and row_result["head_center_range"] > head_limit:
                errors.append(f"{state}: head center drifts {row_result['head_center_range']} px; limit is {head_limit}")
            if state != "running" and row_result["alpha_center_range"] > silhouette_limit:
                errors.append(f"{state}: full silhouette drifts {row_result['alpha_center_range']} px; limit is {silhouette_limit}")
            if iou < iou_limit:
                errors.append(f"{state}: first-to-last silhouette IoU is {iou:.4f}; minimum is {iou_limit}")

        first_unused = 7 if state == "idle" else count
        for column in range(first_unused, 8):
            unused = atlas.crop((column * CELL_W, row * CELL_H, (column + 1) * CELL_W, (row + 1) * CELL_H))
            if unused.getchannel("A").getbbox() is not None:
                errors.append(f"{state}: unused column {column} is not transparent")

    heights_by_state = {
        state: [box[3] - box[1] for box in [alpha_bbox(atlas.crop((column * CELL_W, row * CELL_H, (column + 1) * CELL_W, (row + 1) * CELL_H))) for column in range(FRAME_COUNTS[row])] if box]
        for row, state in enumerate(STATE_NAMES)
        if state in GROUNDED_STATES
    }
    medians = {state: sorted(values)[len(values) // 2] for state, values in heights_by_state.items()}
    for state, height in medians.items():
        if not NEUTRAL_HEIGHT_RANGE[0] <= height <= NEUTRAL_HEIGHT_RANGE[1]:
            errors.append(
                f"{state}: median visible height is {height} px; "
                f"expected {NEUTRAL_HEIGHT_RANGE[0]}-{NEUTRAL_HEIGHT_RANGE[1]} px"
            )
    if medians and max(medians.values()) - min(medians.values()) > 3:
        errors.append(f"grounded state median heights differ too much: {medians}")

    baselines = {
        row["state"]: row["median_baseline"]
        for row in rows
        if row["state"] in heights_by_state
    }
    for state, baseline in baselines.items():
        if not GROUNDED_BASELINE_RANGE[0] <= baseline <= GROUNDED_BASELINE_RANGE[1]:
            errors.append(
                f"{state}: median baseline is {baseline} px; "
                f"expected {GROUNDED_BASELINE_RANGE[0]}-{GROUNDED_BASELINE_RANGE[1]} px"
            )

    return {
        "ok": not errors,
        "file": str(path),
        "errors": errors,
        "rows": rows,
        "grounded_median_heights": medians,
        "grounded_median_baselines": baselines,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("atlas", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    result = inspect(args.atlas.resolve())
    output = json.dumps(result, indent=2)
    print(output)
    if args.json_out:
        args.json_out.write_text(output + "\n", encoding="utf-8")
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
