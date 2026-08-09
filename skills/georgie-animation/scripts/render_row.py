#!/usr/bin/env python3
"""Render one extracted row as a looping GIF for motion review."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frames_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--duration", type=int, default=160)
    args = parser.parse_args()

    paths = sorted(args.frames_dir.glob("*.png"))
    if not paths:
        raise SystemExit(f"no PNG frames found in {args.frames_dir}")
    frames = [Image.open(path).convert("RGBA") for path in paths]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        args.output,
        save_all=True,
        append_images=frames[1:],
        duration=args.duration,
        loop=0,
        disposal=2,
    )


if __name__ == "__main__":
    main()
