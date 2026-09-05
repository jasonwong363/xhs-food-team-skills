#!/usr/bin/env python3
"""Copy an approved image plan into A01-style folders while preserving originals."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

CATEGORY_LABELS = {
    "dish_closeup": "菜品特写",
    "table_spread": "菜品全家福",
    "environment": "门店环境",
    "storefront": "门头图",
    "dish_combo": "组合菜品",
    "preparation": "制作动作",
    "unconfirmed": "待核对",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan")
    parser.add_argument("output")
    parser.add_argument("--expected-groups", type=int)
    parser.add_argument("--min-images", type=int, default=3)
    parser.add_argument("--max-images", type=int, default=5)
    parser.add_argument("--allow-reuse", action="store_true")
    args = parser.parse_args()
    if not 3 <= args.min_images <= args.max_images <= 5:
        raise ValueError("Note groups must stay within 3 to 5 images")

    output = Path(args.output).resolve()
    groups = json.loads(Path(args.plan).resolve().read_text(encoding="utf-8-sig"))
    if not isinstance(groups, list):
        raise ValueError("Plan root must be a JSON array")
    if args.expected_groups is not None and len(groups) != args.expected_groups:
        raise ValueError(f"Expected {args.expected_groups} groups, got {len(groups)}")

    seen_ids: set[str] = set()
    seen_sources: set[Path] = set()
    manifest = []
    validated = []
    for group in groups:
        group_id = group.get("id", "")
        images = group.get("images", [])
        if not group_id or group_id in seen_ids or group_id in ('.', '..') or any(c in group_id for c in '/\\:'):
            raise ValueError(f"Invalid or duplicate group id: {group_id!r}")
        if (output / group_id).exists():
            raise ValueError(f"Group already exists: {group_id}")
        if not args.min_images <= len(images) <= args.max_images:
            raise ValueError(f"{group_id} must contain {args.min_images} to {args.max_images} images")
        orders = sorted(item.get("order") for item in images)
        if orders != list(range(1, len(images) + 1)):
            raise ValueError(f"{group_id} orders must be consecutive from 1")
        ordered_images = sorted(images, key=lambda value: value["order"])
        if not group.get("note_id") or not group.get("note_subject"):
            raise ValueError(f"{group_id} needs a note id and subject before grouping")
        if ordered_images[0].get("category") != "dish_closeup":
            raise ValueError(f"{group_id} cover must be a single dish")
        if ordered_images[1].get("category") != "table_spread":
            raise ValueError(f"{group_id} second image must be a table spread")
        if len({str(Path(item['source']).resolve()) for item in images}) != len(images):
            raise ValueError(f"{group_id} repeats an image within the note")
        if ordered_images[0].get("role") != "cover":
            raise ValueError(f"{group_id} first image role must be cover")

        prepared = []
        for item in ordered_images:
            if not item.get("match_reason"):
                raise ValueError(f"{group_id} requires a text-match reason for every image")
            category = item.get("category")
            if category not in CATEGORY_LABELS:
                raise ValueError(f"{group_id} has invalid category: {category!r}")
            source = Path(item["source"]).resolve()
            if not source.is_file():
                raise FileNotFoundError(source)
            if source in seen_sources and not args.allow_reuse:
                raise ValueError(f"Image reused across groups: {source}")
            seen_sources.add(source)
            prepared.append((item, source))
        seen_ids.add(group_id)
        validated.append((group, prepared))

    output.mkdir(parents=True, exist_ok=True)
    for group, prepared in validated:
        group_id = group["id"]
        group_dir = output / group_id
        group_dir.mkdir(parents=True, exist_ok=False)
        for item, source in prepared:
            safe_name = f"{item['order']:02d}-{CATEGORY_LABELS[item['category']]}-{source.name}"
            destination = group_dir / safe_name
            shutil.copy2(source, destination)
            manifest.append({
                "group_id": group_id,
                **item,
                "source": str(source),
                "copied_to": str(destination),
            })

    (output / "group-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Created {len(groups)} groups with {len(manifest)} unique image assignments under {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
