#!/usr/bin/env python3
"""Extract complete poses with one shared scale and one body anchor."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


CELL_SIZE = (192, 208)
TARGET_HEIGHT = 176
BASELINE = 203
FRAME_COUNTS = {
    "idle": 6,
    "running-right": 8,
    "running-left": 8,
    "waving": 4,
    "jumping": 5,
    "failed": 8,
    "waiting": 6,
    "running": 6,
    "review": 6,
    "look-cardinals": 4,
    "look-row-9": 8,
    "look-row-10": 8,
}


def parse_color(value: str) -> tuple[int, int, int]:
    value = value.removeprefix("#")
    if len(value) != 6:
        raise SystemExit("chroma key must use #RRGGBB")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def remove_key(image: Image.Image, key: tuple[int, int, int], threshold: int) -> Image.Image:
    rgba = image.convert("RGBA")
    limit = threshold * threshold
    key_channel = max(range(3), key=lambda index: key[index])
    other_channels = [index for index in range(3) if index != key_channel]
    dominant_key = all(key[key_channel] - key[index] >= 128 for index in other_channels)
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            red, green, blue, _ = pixels[x, y]
            color = (red, green, blue)
            distance = sum((color[index] - key[index]) ** 2 for index in range(3))
            dominant_spill = (
                dominant_key
                and color[key_channel] >= 50
                and color[key_channel] - max(color[index] for index in other_channels) >= 5
            )
            if distance <= limit or dominant_spill:
                pixels[x, y] = (0, 0, 0, 0)
    return rgba


def clear_gap_boundaries(strip: Image.Image, count: int, minimum_gap: int = 4) -> list[int] | None:
    alpha = strip.getchannel("A")
    data = alpha.tobytes()
    occupied = [False] * strip.width
    for y in range(strip.height):
        offset = y * strip.width
        for x in range(strip.width):
            if data[offset + x] > 16:
                occupied[x] = True

    gaps: list[tuple[int, int]] = []
    start = None
    for x, value in enumerate(occupied + [True]):
        if not value and start is None:
            start = x
        elif value and start is not None:
            gaps.append((start, x))
            start = None

    slot_width = strip.width / count
    boundaries = [0]
    for index in range(1, count):
        expected = index * slot_width
        candidates = [
            gap
            for gap in gaps
            if gap[1] - gap[0] >= minimum_gap
            and abs((gap[0] + gap[1]) / 2 - expected) <= slot_width * 0.4
        ]
        if not candidates:
            return None
        chosen = max(
            candidates,
            key=lambda gap: (gap[1] - gap[0], -abs((gap[0] + gap[1]) / 2 - expected)),
        )
        boundaries.append(round((chosen[0] + chosen[1]) / 2))
    boundaries.append(strip.width)
    return boundaries


def body_anchor(sprite: Image.Image) -> float:
    alpha = sprite.getchannel("A")
    width, height = sprite.size
    start_y = round(height * 0.45)
    stop_y = round(height * 0.80)
    xs = [
        x
        for y in range(start_y, stop_y)
        for x in range(width)
        if alpha.getpixel((x, y)) > 16
    ]
    if not xs:
        return width / 2
    return sum(xs) / len(xs)


def extract(
    source: Path,
    state: str,
    output_dir: Path,
    key: tuple[int, int, int],
    threshold: int,
    target_height: int,
) -> None:
    count = FRAME_COUNTS[state]
    strip = remove_key(Image.open(source), key, threshold)
    slot_width = strip.width / count
    boundaries = [round(index * slot_width) for index in range(count + 1)]
    slots = [strip.crop((boundaries[index], 0, boundaries[index + 1], strip.height)) for index in range(count)]
    boxes = [slot.getbbox() for slot in slots]
    if any(box is None for box in boxes):
        raise SystemExit(f"{state}: at least one frame is empty after chroma removal")

    typed_boxes = [box for box in boxes if box is not None]
    equal_slots_pass = True
    for slot, box in zip(slots, typed_boxes):
        safe_margin = max(8, round(slot.width * 0.04))
        if box[0] < safe_margin or slot.width - box[2] < safe_margin:
            equal_slots_pass = False
            break
    extraction_mode = "equal-slots"
    if not equal_slots_pass:
        boundaries = clear_gap_boundaries(strip, count)
        if boundaries is None:
            raise SystemExit(
                f"{state}: pose crosses its equal slot and no certified empty gap exists; "
                "regenerate the complete row with smaller separated poses"
            )
        slots = [strip.crop((boundaries[index], 0, boundaries[index + 1], strip.height)) for index in range(count)]
        boxes = [slot.getbbox() for slot in slots]
        if any(box is None for box in boxes):
            raise SystemExit(f"{state}: clear-gap extraction produced an empty frame")
        typed_boxes = [box for box in boxes if box is not None]
        extraction_mode = "clear-gaps"
    median_height = sorted(box[3] - box[1] for box in typed_boxes)[count // 2]
    scale = target_height / median_height
    source_ground = max(box[3] for box in typed_boxes)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_sizes = []
    written_frames: list[Image.Image] = []
    for index, (slot, box) in enumerate(zip(slots, typed_boxes)):
        sprite = slot.crop(box)
        output_size = (round(sprite.width * scale), round(sprite.height * scale))
        if output_size[0] > CELL_SIZE[0] - 8 or output_size[1] > CELL_SIZE[1] - 5:
            raise SystemExit(
                f"{state} frame {index}: pose would be {output_size[0]}x{output_size[1]} at "
                f"target height {target_height}; regenerate a more compact complete row"
            )
        anchor = body_anchor(sprite) * scale
        resized = sprite.resize(output_size, Image.Resampling.LANCZOS)
        frame = Image.new("RGBA", CELL_SIZE, (0, 0, 0, 0))
        target_bottom = BASELINE
        if state == "jumping":
            target_bottom -= round((source_ground - box[3]) * scale)
        target_top = target_bottom - resized.height
        if state == "jumping":
            target_top = max(8, target_top)
        frame.alpha_composite(resized, (round(CELL_SIZE[0] / 2 - anchor), target_top))
        frame_box = frame.getbbox()
        if frame_box is None:
            raise SystemExit(f"{state} frame {index}: registered pose is empty")
        registered_anchor = frame_box[0] + body_anchor(frame.crop(frame_box))
        correction = round(CELL_SIZE[0] / 2 - registered_anchor)
        if correction:
            corrected = Image.new("RGBA", CELL_SIZE, (0, 0, 0, 0))
            corrected.alpha_composite(frame, (correction, 0))
            frame = corrected
        written_frames.append(frame.copy())
        frame.save(output_dir / f"{index:02d}.png")
        output_sizes.append(output_size)

    if state == "jumping" and written_frames:
        written_frames[0].save(output_dir / f"{count - 1:02d}.png")
    if state == "failed" and len(written_frames) == 8:
        written_frames[2].save(output_dir / "04.png")
        written_frames[1].save(output_dir / "05.png")
        written_frames[0].save(output_dir / "07.png")

    print(
        f"{state}: frames={count} target_height={target_height} "
        f"scale={scale:.4f} widths={min(size[0] for size in output_sizes)}-{max(size[0] for size in output_sizes)} "
        f"heights={min(size[1] for size in output_sizes)}-{max(size[1] for size in output_sizes)} "
        f"baseline={BASELINE} mode={extraction_mode}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("state", choices=FRAME_COUNTS)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--chroma-key", default="#0000FF")
    parser.add_argument("--key-threshold", type=int, default=160)
    parser.add_argument("--target-height", type=int, default=TARGET_HEIGHT)
    args = parser.parse_args()
    extract(
        args.source.resolve(),
        args.state,
        args.output_dir.resolve(),
        parse_color(args.chroma_key),
        args.key_threshold,
        args.target_height,
    )


if __name__ == "__main__":
    main()
