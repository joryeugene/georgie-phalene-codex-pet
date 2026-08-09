#!/usr/bin/env python3
"""Build Georgie's running row from one generated body and four generated tail keys."""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image

from extract_row import BASELINE, CELL_SIZE, TARGET_HEIGHT, parse_color, remove_key


SEQUENCE = (0, 1, 2, 3, 2, 1)
HIP_ANCHOR = (115, 132)


def components(image: Image.Image) -> list[tuple[int, tuple[int, int, int, int]]]:
    alpha = image.getchannel("A")
    width, height = alpha.size
    data = bytearray(alpha.tobytes())
    seen = bytearray(width * height)
    found: list[tuple[int, tuple[int, int, int, int]]] = []
    for start, value in enumerate(data):
        if value <= 16 or seen[start]:
            continue
        queue = deque([start])
        seen[start] = 1
        count = 0
        min_x = max_x = start % width
        min_y = max_y = start // width
        while queue:
            current = queue.popleft()
            y, x = divmod(current, width)
            count += 1
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
            neighbors = []
            if x:
                neighbors.append(current - 1)
            if x + 1 < width:
                neighbors.append(current + 1)
            if y:
                neighbors.append(current - width)
            if y + 1 < height:
                neighbors.append(current + width)
            for neighbor in neighbors:
                if data[neighbor] > 16 and not seen[neighbor]:
                    seen[neighbor] = 1
                    queue.append(neighbor)
        if count >= 100:
            found.append((count, (min_x, min_y, max_x + 1, max_y + 1)))
    return found


def root_y(tail: Image.Image) -> float:
    alpha = tail.getchannel("A")
    points = [
        y
        for x in range(min(14, tail.width))
        for y in range(tail.height)
        if alpha.getpixel((x, y)) > 16
    ]
    if not points:
        raise SystemExit("tail key has no visible root")
    return sum(points) / len(points)


def build(source: Path, output_dir: Path, key: tuple[int, int, int], threshold: int) -> None:
    keyed = remove_key(Image.open(source), key, threshold)
    found = sorted(components(keyed), reverse=True)
    if len(found) != 5:
        raise SystemExit(f"expected one body and four tail keys; found {len(found)} components")

    body_box = found[0][1]
    tail_boxes = sorted((box for _, box in found[1:]), key=lambda box: box[0])
    body = keyed.crop(body_box)
    tails = [keyed.crop(box) for box in tail_boxes]
    scale = TARGET_HEIGHT / body.height
    body = body.resize((round(body.width * scale), TARGET_HEIGHT), Image.Resampling.LANCZOS)
    tails = [
        tail.resize((round(tail.width * scale), round(tail.height * scale)), Image.Resampling.LANCZOS)
        for tail in tails
    ]
    source_root_ys = [root_y(keyed.crop(box)) * scale for box in tail_boxes]

    output_dir.mkdir(parents=True, exist_ok=True)
    body_position = (round(CELL_SIZE[0] / 2 - body.width / 2), BASELINE - body.height)
    for frame_index, tail_index in enumerate(SEQUENCE):
        frame = Image.new("RGBA", CELL_SIZE, (0, 0, 0, 0))
        tail = tails[tail_index]
        tail_position = (HIP_ANCHOR[0], round(HIP_ANCHOR[1] - source_root_ys[tail_index]))
        frame.alpha_composite(tail, tail_position)
        frame.alpha_composite(body, body_position)
        box = frame.getbbox()
        if box is None or box[0] < 4 or box[1] < 4 or box[2] > CELL_SIZE[0] - 4 or box[3] > CELL_SIZE[1] - 4:
            raise SystemExit(f"frame {frame_index} clips the cell safe area: {box}")
        frame.save(output_dir / f"{frame_index:02d}.png")

    print(
        f"running: frames=6 body={body.width}x{body.height} baseline={BASELINE} "
        f"hip={HIP_ANCHOR} sequence=A-B-C-D-C-B"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("component_kit", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--chroma-key", default="#0000FF")
    parser.add_argument("--key-threshold", type=int, default=160)
    args = parser.parse_args()
    build(
        args.component_kit.resolve(),
        args.output_dir.resolve(),
        parse_color(args.chroma_key),
        args.key_threshold,
    )


if __name__ == "__main__":
    main()
