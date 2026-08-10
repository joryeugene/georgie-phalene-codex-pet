#!/usr/bin/env python3
"""Build pointer row 9 by mirroring only the approved row 10 eye motion."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


EYE_BOXES = ((60, 56, 79, 76), (88, 56, 108, 76))


def mirror_eye_gaze(frame: Image.Image) -> Image.Image:
    output = frame.convert("RGBA")
    for left, top, right, bottom in EYE_BOXES:
        patch = output.crop((left, top, right, bottom)).transpose(
            Image.Transpose.FLIP_LEFT_RIGHT
        )
        mask = Image.new("L", patch.size, 0)
        ImageDraw.Draw(mask).ellipse((1, 1, patch.width - 2, patch.height - 2), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(1.2))
        output.paste(patch, (left, top), mask)
    return output


def build(row_10_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    # Reuse the nearest approved up-gaze pose for 000 and 022.5 degrees. Only
    # the two eye masks change, so the body and tail stay registered at 180/000.
    source_indexes = (7, 7, 6, 5, 4, 3, 2, 1)
    for output_index, source_index in enumerate(source_indexes):
        source = row_10_dir / f"{source_index:02d}.png"
        with Image.open(source) as opened:
            mirror_eye_gaze(opened).save(output_dir / f"{output_index:02d}.png")

    print("pointer-row-9: mirrored eye motion from row-10 frames 7, 7, 6, 5, 4, 3, 2, 1")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("row_10_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    build(args.row_10_dir.resolve(), args.output_dir.resolve())


if __name__ == "__main__":
    main()
