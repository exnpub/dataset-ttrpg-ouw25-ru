#!/usr/bin/env python3
"""Compare DOCX structure with normalized Markdown and write a QA report.

This audit is deliberately structural. A passed audit does not replace visual
or semantic review; it identifies the documents that deserve it first.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{WORD_NS}}}"
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
HEADING_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)
EXTERNAL_LINK_RE = re.compile(r"\[[^\]]+\]\(https?://")
DRAFT_LINK_RE = re.compile(r"\\?<https?://|\\<\[[^\]]+\]\(")
MARKDOWN_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*$", re.MULTILINE)
HTML_TABLE_RE = re.compile(r"<table\b", re.IGNORECASE)


def read_docx_structure(path: Path) -> dict[str, int]:
    with zipfile.ZipFile(path) as archive:
        media = sum(name.startswith("word/media/") and not name.endswith("/") for name in archive.namelist())
        document = ElementTree.fromstring(archive.read("word/document.xml"))
        paragraphs = document.findall(".//w:p", {"w": WORD_NS})
        headings = 0
        for paragraph in paragraphs:
            style = paragraph.find("w:pPr/w:pStyle", {"w": WORD_NS})
            style_name = "" if style is None else style.get(f"{W}val", "")
            if style_name.lower().startswith(("heading", "заголовок")):
                headings += 1
        tables = len(document.findall(".//w:tbl", {"w": WORD_NS}))
        hyperlinks = len(document.findall(".//w:hyperlink", {"w": WORD_NS}))
    return {
        "media": media,
        "tables": tables,
        "headings": headings,
        "hyperlinks": hyperlinks,
    }


def read_markdown_structure(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8")
    return {
        "images": len(IMAGE_RE.findall(text)),
        "tables": len(MARKDOWN_TABLE_SEPARATOR_RE.findall(text)) + len(HTML_TABLE_RE.findall(text)),
        "headings": len(HEADING_RE.findall(text)),
        "external_links": len(EXTERNAL_LINK_RE.findall(text)),
        "draft_links": len(DRAFT_LINK_RE.findall(text)),
        "characters": len(text),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    manifest_path = root / "content" / "manifests" / "documents.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    results: list[dict[str, object]] = []

    for document in manifest["documents"]:
        source_path = root / str(document["source_path"])
        markdown_path = root / str(document["markdown_path"])
        source = read_docx_structure(source_path)
        markdown = read_markdown_structure(markdown_path)
        flags: list[dict[str, str]] = []
        if source["media"] != markdown["images"]:
            flags.append(
                {
                    "kind": "media_count_mismatch",
                    "severity": "high",
                    "message": "Число вложений DOCX и изображений Markdown различается.",
                }
            )
        if source["tables"] and not markdown["tables"]:
            flags.append(
                {
                    "kind": "tables_not_detected",
                    "severity": "review",
                    "message": "В DOCX есть таблицы, но в Markdown не найдена табличная разметка.",
                }
            )
        if source["headings"] and markdown["headings"] <= 1:
            flags.append(
                {
                    "kind": "headings_not_detected",
                    "severity": "review",
                    "message": "В DOCX есть стилевые заголовки, но Markdown не сохранил структуру.",
                }
            )
        if markdown["draft_links"]:
            flags.append(
                {
                    "kind": "draft_link_remaining",
                    "severity": "high",
                    "message": "Найден draft-формат внешней ссылки.",
                }
            )
        if markdown["characters"] < 200:
            flags.append(
                {
                    "kind": "short_document",
                    "severity": "review",
                    "message": "Нормализованный текст очень короткий; сверить с DOCX.",
                }
            )
        results.append(
            {
                "document_id": document["id"],
                "source_path": document["source_path"],
                "markdown_path": document["markdown_path"],
                "source": source,
                "markdown": markdown,
                "flags": flags,
            }
        )

    priority = [result for result in results if result["flags"]]
    high = sum(
        flag["severity"] == "high" for result in priority for flag in result["flags"]
    )
    report = {
        "schema_version": 1,
        "generated_at": dt.date.today().isoformat(),
        "scope": "structural comparison; not a semantic or visual approval",
        "summary": {
            "documents": len(results),
            "documents_needing_review": len(priority),
            "high_severity_flags": high,
        },
        "documents": results,
    }
    destination = root / "content" / "manifests" / "conversion-audit.json"
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Audited {len(results)} documents: {len(priority)} need review, "
        f"{high} high-severity findings."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
