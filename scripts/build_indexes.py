#!/usr/bin/env python3
"""Build document and chunk JSONL indexes from normalized Markdown."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


FRONT_MATTER_RE = re.compile(r"\A---\n(?P<data>.*?)\n---\n(?:\n)?", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
IMAGE_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\([^)]+\)")
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
FORM_FIELD_RE = re.compile(r"(?m)^\s*(?:[-*+]\s+)?\[Поле для заполнения\]\s*$")


def parse_front_matter(text: str) -> tuple[dict[str, object], str]:
    match = FRONT_MATTER_RE.match(text)
    if not match:
        raise ValueError("missing YAML front matter")
    metadata: dict[str, object] = {}
    for line in match.group("data").splitlines():
        key, separator, value = line.partition(": ")
        if not separator:
            continue
        if value in {"true", "false", "null"} or value.startswith(("\"", "[", "{")):
            metadata[key] = json.loads(value)
        else:
            metadata[key] = value
    return metadata, text[match.end() :]


def clean_for_index(text: str) -> str:
    text = COMMENT_RE.sub("", text)
    text = IMAGE_RE.sub(
        lambda match: ""
        if match.group("alt") == "Изображение — требуется описание"
        else f"[Изображение: {match.group('alt')}]",
        text,
    )
    # The label of a form question is useful for retrieval; a blank response
    # field is not. Keep it in Markdown for human use, but omit it from JSONL.
    text = FORM_FIELD_RE.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def split_large_block(block: str, maximum: int) -> list[str]:
    if len(block) <= maximum:
        return [block]
    sentences = re.split(r"(?<=[.!?…])\s+", block)
    parts: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > maximum:
            parts.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts


def make_chunks(body: str, title: str, maximum: int) -> list[tuple[list[str], str]]:
    """Split at useful structural boundaries, retaining local field labels."""
    headings = [title]
    blocks: list[tuple[list[str], int, int, str]] = []
    current: list[str] = []
    heading_level = 1
    section_number = 0
    emitted_headers: set[int] = set()

    def flush() -> None:
        nonlocal current
        value = "\n".join(current).strip()
        if value:
            if heading_level > 1 and section_number not in emitted_headers:
                value = f"{'#' * heading_level} {headings[-1]}\n\n{value}"
            emitted_headers.add(section_number)
            blocks.append((headings.copy(), heading_level, section_number, value))
        current = []

    for line in body.splitlines():
        match = HEADING_RE.match(line)
        if match:
            flush()
            heading_level = len(match.group(1))
            section_number += 1
            if heading_level == 1:
                headings = [match.group(2)]
            else:
                headings = headings[: heading_level - 1]
                headings.append(match.group(2))
            continue
        if not line.strip() and current:
            flush()
            continue
        if line.strip():
            current.append(line)
    flush()

    chunks: list[tuple[list[str], str]] = []
    active_path: list[str] | None = None
    active_section: int | None = None
    current_text = ""
    for path, level, section, block in blocks:
        for part in split_large_block(block, maximum):
            new_major_section = section != active_section and level <= 4
            if current_text and (
                new_major_section or len(current_text) + len(part) + 2 > maximum
            ):
                if current_text:
                    chunks.append((active_path or [title], current_text))
                active_path = path
                active_section = section
                current_text = part
            else:
                if not current_text:
                    active_path = path
                    active_section = section
                current_text = f"{current_text}\n\n{part}".strip()
    if current_text:
        chunks.append((active_path or [title], current_text))
    return chunks


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--max-chars", type=int, default=3200)
    args = parser.parse_args()
    if args.max_chars < 500:
        parser.error("--max-chars must be at least 500")

    root = args.root.resolve()
    markdown_root = root / "content" / "markdown"
    index_root = root / "content" / "indexes"
    chunks_root = root / "content" / "chunks"
    index_root.mkdir(parents=True, exist_ok=True)
    chunks_root.mkdir(parents=True, exist_ok=True)

    documents: list[dict[str, object]] = []
    chunks: list[dict[str, object]] = []
    for path in sorted(markdown_root.glob("*.md")):
        metadata, body = parse_front_matter(path.read_text(encoding="utf-8"))
        body = clean_for_index(body)
        document_id = str(metadata["id"])
        document = {
            "document_id": document_id,
            "title": metadata["title"],
            "source_path": metadata["source_path"],
            "markdown_path": path.relative_to(root).as_posix(),
            "document_type": metadata["document_type"],
            "section": metadata["section"],
            "language": metadata["language"],
            "license": metadata["license"],
            "license_scope": metadata["license_scope"],
            "asset_license": metadata["asset_license"],
            "status": metadata["status"],
            "text": body,
            "text_sha256": sha256_text(body),
        }
        documents.append(document)
        for number, (heading_path, chunk_text) in enumerate(
            make_chunks(body, str(metadata["title"]), args.max_chars), start=1
        ):
            chunk_id = f"{document_id}--{number:04d}"
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "chunk_number": number,
                    "heading_path": heading_path,
                    "document_type": metadata["document_type"],
                    "section": metadata["section"],
                    "language": metadata["language"],
                    "license": metadata["license"],
                    "license_scope": metadata["license_scope"],
                    "status": metadata["status"],
                    "text": chunk_text,
                    "text_sha256": sha256_text(chunk_text),
                }
            )

    def write_jsonl(destination: Path, rows: list[dict[str, object]]) -> None:
        destination.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )

    write_jsonl(index_root / "documents.jsonl", documents)
    write_jsonl(chunks_root / "chunks.jsonl", chunks)
    print(f"Indexed {len(documents)} documents into {len(chunks)} chunks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
