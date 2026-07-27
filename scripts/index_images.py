#!/usr/bin/env python3
"""Build an index of all images referenced in the normalized Markdown."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


FRONT_MATTER_RE = re.compile(r"\A---\n(?P<data>.*?)\n---\n(?:\n)?", re.DOTALL)
IMAGE_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)")


def parse_front_matter(text: str) -> dict[str, object]:
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}
    metadata: dict[str, object] = {}
    for line in match.group("data").splitlines():
        key, separator, value = line.partition(": ")
        if not separator:
            continue
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        
        # Simple type conversion for known fields
        if value.lower() == "true":
            metadata[key] = True
        elif value.lower() == "false":
            metadata[key] = False
        elif value.lower() == "null":
            metadata[key] = None
        else:
            metadata[key] = value
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    root = args.root.resolve()
    markdown_root = root / "content" / "markdown"
    index_path = root / "content" / "indexes" / "images.jsonl"
    
    index_path.parent.mkdir(parents=True, exist_ok=True)

    images: list[dict[str, object]] = []
    for md_path in sorted(markdown_root.glob("*.md")):
        try:
            content = md_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading {md_path}: {e}")
            continue

        metadata = parse_front_matter(content)
        document_id = str(metadata.get("id", md_path.stem))
        
        # Find all images and their line numbers
        lines = content.splitlines()
        for line_num, line in enumerate(lines, start=1):
            for match in IMAGE_RE.finditer(line):
                alt = match.group("alt")
                path = match.group("path")
                
                # Resolve relative path to project root
                # Paths in MD are relative to the MD file, e.g., ../assets/...
                img_abs_path = (md_path.parent / path).resolve()
                try:
                    rel_path = img_abs_path.relative_to(root).as_posix()
                except ValueError:
                    rel_path = path

                # Determine status
                if alt == "Изображение — требуется описание":
                    status = "needs_review"
                elif "декоративн" in alt.lower() or "decorative" in alt.lower():
                    status = "decorative"
                else:
                    status = "ok"

                images.append({
                    "document_id": document_id,
                    "document_title": metadata.get("title", md_path.stem),
                    "alt": alt,
                    "path": rel_path,
                    "line": line_num,
                    "status": status,
                    "markdown_path": md_path.relative_to(root).as_posix()
                })

    with index_path.open("w", encoding="utf-8") as f:
        for img in images:
            f.write(json.dumps(img, ensure_ascii=False) + "\n")

    print(f"Indexed {len(images)} images from {len(sorted(markdown_root.glob('*.md')))} documents.")
    print(f"Output saved to {index_path.relative_to(root)}")
    
    # Summary
    needs_review = sum(1 for img in images if img["status"] == "needs_review")
    print(f"Summary: {len(images)} total, {needs_review} need description.")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
