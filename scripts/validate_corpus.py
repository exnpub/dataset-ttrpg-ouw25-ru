#!/usr/bin/env python3
"""Validate source traceability and structural invariants of the ML corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


FRONT_MATTER_RE = re.compile(r"\A---\n(?P<data>.*?)\n---\n", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+", re.MULTILINE)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\((?P<path>[^)]+)\)")
DRAFT_LINK_RE = re.compile(
    r"\\?<https?://(?:[^<>\\\s]|\\(?!>))+?\\?>|\\<\[[^\]]+\]\([^)]+\)"
)
TRAILING_ESCAPE_IN_LINK_RE = re.compile(r"\]\([^\n)]*\\\)")


def parse_front_matter(text: str) -> dict[str, object]:
    match = FRONT_MATTER_RE.match(text)
    if not match:
        raise ValueError("missing YAML front matter")
    result: dict[str, object] = {}
    for line in match.group("data").splitlines():
        key, separator, value = line.partition(": ")
        if separator:
            result[key] = json.loads(value) if value.startswith(("\"", "[")) else value
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    markdown_root = root / "content" / "markdown"
    manifest_path = root / "content" / "manifests" / "documents.json"
    errors: list[str] = []
    manifest_ids: set[str] = set()
    markdown_ids: set[str] = set()

    if not manifest_path.exists():
        errors.append(f"missing manifest: {manifest_path.relative_to(root)}")
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        records = manifest.get("documents", [])
        source_count = len(list((root / "docx_sources").rglob("*.docx")))
        if len(records) != source_count:
            errors.append(f"manifest has {len(records)} documents, source has {source_count}")
        for record in records:
            document_id = str(record.get("id", ""))
            if document_id in manifest_ids:
                errors.append(f"manifest contains duplicate id: {document_id}")
            manifest_ids.add(document_id)

    for path in sorted(markdown_root.glob("*.md")):
        relative = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        try:
            metadata = parse_front_matter(text)
        except ValueError as error:
            errors.append(f"{relative}: {error}")
            continue
        required = {
            "id",
            "title",
            "source_path",
            "source_sha256",
            "license",
            "license_scope",
            "asset_license",
            "status",
        }
        missing = required.difference(metadata)
        if missing:
            errors.append(f"{relative}: missing front-matter keys: {', '.join(sorted(missing))}")
        if metadata.get("license") != "Public Domain" or metadata.get("license_scope") != "text":
            errors.append(f"{relative}: unexpected text license declaration")
        document_id = str(metadata.get("id", ""))
        if document_id in markdown_ids:
            errors.append(f"{relative}: duplicate Markdown id: {document_id}")
        markdown_ids.add(document_id)
        source = root / str(metadata.get("source_path", ""))
        if not source.is_file():
            errors.append(f"{relative}: source DOCX does not exist")
        elif metadata.get("source_sha256") != sha256(source):
            errors.append(f"{relative}: source DOCX hash does not match front matter")
        headings = [len(match.group(1)) for match in HEADING_RE.finditer(text)]
        if headings.count(1) != 1:
            errors.append(f"{relative}: expected exactly one H1, found {headings.count(1)}")
        if any(level == 1 for level in headings[1:]):
            errors.append(f"{relative}: H1 is not the first heading")
        if any(current > previous + 1 for previous, current in zip(headings, headings[1:])):
            errors.append(f"{relative}: heading hierarchy contains a skipped level")
        if "/private/tmp/" in text or "/var/folders/" in text:
            errors.append(f"{relative}: contains a temporary absolute path")
        if DRAFT_LINK_RE.search(text):
            errors.append(f"{relative}: contains a draft-style external link")
        if TRAILING_ESCAPE_IN_LINK_RE.search(text):
            errors.append(f"{relative}: Markdown link destination ends with an escape")
        for match in IMAGE_RE.finditer(text):
            asset = (path.parent / match.group("path")).resolve()
            if not asset.exists():
                errors.append(f"{relative}: missing image asset {match.group('path')}")

    if manifest_ids and markdown_ids != manifest_ids:
        errors.append("manifest and Markdown document IDs do not match")

    documents_index = root / "content" / "indexes" / "documents.jsonl"
    chunks_index = root / "content" / "chunks" / "chunks.jsonl"
    if not documents_index.exists() or not chunks_index.exists():
        errors.append("missing JSONL indexes; run scripts/build_indexes.py")
    else:
        documents = read_jsonl(documents_index)
        chunks = read_jsonl(chunks_index)
        indexed_ids = {str(row.get("document_id", "")) for row in documents}
        if indexed_ids != markdown_ids or len(documents) != len(indexed_ids):
            errors.append("documents.jsonl does not have exactly one row per Markdown document")
        chunk_ids: set[str] = set()
        for chunk in chunks:
            chunk_id = str(chunk.get("chunk_id", ""))
            if not chunk_id or chunk_id in chunk_ids:
                errors.append(f"chunks.jsonl has missing or duplicate chunk id: {chunk_id}")
            chunk_ids.add(chunk_id)
            if str(chunk.get("document_id", "")) not in indexed_ids:
                errors.append(f"{chunk_id}: references an unknown document")
            chunk_text = str(chunk.get("text", ""))
            if not chunk_text.strip():
                errors.append(f"{chunk_id}: has empty text")
            if "[Поле для заполнения]" in chunk_text:
                errors.append(f"{chunk_id}: indexes an empty template field")
            if chunk.get("license") != "Public Domain" or chunk.get("license_scope") != "text":
                errors.append(f"{chunk_id}: missing or incorrect text license metadata")

    if errors:
        print("Corpus validation failed:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"Corpus validation passed for {len(list(markdown_root.glob('*.md')))} Markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
