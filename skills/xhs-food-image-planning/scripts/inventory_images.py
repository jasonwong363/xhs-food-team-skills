#!/usr/bin/env python3
"""Create an image metadata inventory and contact sheets without changing originals."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def dhash(image: Image.Image, size: int = 8) -> str:
    gray = image.convert("L").resize((size + 1, size))
    pixels = list(gray.getdata())
    bits = []
    for y in range(size):
        row = y * (size + 1)
        bits.extend(pixels[row + x] > pixels[row + x + 1] for x in range(size))
    return f"{sum(int(bit) << i for i, bit in enumerate(bits)):016x}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("output")
    parser.add_argument("--per-page", type=int, default=20)
    parser.add_argument("--limit", type=int, help="Only inventory the first N sorted images for workflow testing")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in source.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSIONS)
    if args.limit is not None:
        if args.limit < 1:
            raise ValueError("--limit must be at least 1")
        files = files[: args.limit]
    rows, thumbs = [], []
    for index, path in enumerate(files, 1):
        try:
            with Image.open(path) as image:
                orientation = image.getexif().get(274, 1)
                width, height = image.size
                if orientation in (5, 6, 7, 8):
                    width, height = height, width
                image.draft("RGB", (480, 480))
                image = ImageOps.exif_transpose(image)
                image_hash = dhash(image)
                thumb = image.convert("RGB")
                thumb.thumbnail((240, 155))
                thumbs.append((index, path.name, thumb.copy()))
            rows.append([index, str(path), width, height, image_hash, "", "", "", ""])
        except Exception as error:
            rows.append([index, str(path), "", "", "", "unreadable", "reject", "", str(error)])

    with (output / "02-image-order.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sequence", "source", "width", "height", "dhash", "category", "decision", "near_duplicate_group", "notes"])
        writer.writerows(rows)

    font = ImageFont.load_default()
    cols, cell_w, cell_h = 5, 250, 195
    for page in range(math.ceil(len(thumbs) / args.per_page)):
        chunk = thumbs[page * args.per_page:(page + 1) * args.per_page]
        canvas = Image.new("RGB", (cols * cell_w, math.ceil(len(chunk) / cols) * cell_h), "white")
        draw = ImageDraw.Draw(canvas)
        for slot, (index, name, thumb) in enumerate(chunk):
            x, y = (slot % cols) * cell_w, (slot // cols) * cell_h
            canvas.paste(thumb, (x + (cell_w - thumb.width) // 2, y + 4))
            draw.text((x + 5, y + 164), f"{index:04d} {name[:30]}", fill="black", font=font)
        canvas.save(output / f"contact-{page + 1:03d}.jpg", quality=90)

    digest = hashlib.sha256("\n".join(str(p) for p in files).encode("utf-8")).hexdigest()
    (output / "inventory-summary.txt").write_text(f"source={source}\nimages={len(files)}\npath_digest={digest}\n", encoding="utf-8")
    print(f"Inventoried {len(files)} images into {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
