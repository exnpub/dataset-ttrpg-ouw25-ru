#!/usr/bin/env python3
"""Build a reviewable Markdown corpus from the project's DOCX sources.

The script has no Python package dependencies. It deliberately keeps the raw
Pandoc output in ``content/imported`` separate from the normalized Markdown in
``content/markdown``. Re-running the script never overwrites normalized files
unless ``--refresh-markdown`` is passed explicitly.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


CYRILLIC = str.maketrans(
    {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e",
        "ё": "yo", "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k",
        "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
        "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts",
        "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "",
        "э": "e", "ю": "yu", "я": "ya",
        "А": "a", "Б": "b", "В": "v", "Г": "g", "Д": "d", "Е": "e",
        "Ё": "yo", "Ж": "zh", "З": "z", "И": "i", "Й": "y", "К": "k",
        "Л": "l", "М": "m", "Н": "n", "О": "o", "П": "p", "Р": "r",
        "С": "s", "Т": "t", "У": "u", "Ф": "f", "Х": "kh", "Ц": "ts",
        "Ч": "ch", "Ш": "sh", "Щ": "shch", "Ъ": "", "Ы": "y", "Ь": "",
        "Э": "e", "Ю": "yu", "Я": "ya",
    }
)
SECTION_RE = re.compile(r"^(?P<section>\d+(?:\.\d+)*\.?)\s*(?P<title>.+)$")
HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<title>.+?)\s*$", re.MULTILINE)
HTML_IMAGE_RE = re.compile(r'<img\b[^>]*?\bsrc="(?P<path>[^"]+)"[^>]*?/?>', re.I)
MD_IMAGE_RE = re.compile(r"(?P<prefix>!\[[^\]]*\]\()(?P<path>[^)\s]+)(?P<suffix>\))")
ILLUSTRATION_RE = re.compile(r"\\\[(?P<description>ИЛЛЮСТРАЦИЯ:[^\]]+)\\\]", re.I)
ESCAPED_LINK_RE = re.compile(
    r"\\<\[(?P<label>[^\]]+)\]\((?P<url>[^)]+)\)\\>"
)
DRAFT_OPEN_LINK_RE = re.compile(r"\\<(?P<link>\[[^\]]+\]\([^)]+\))")
# Pandoc escapes draft links as ``\<https://example.test\>``.  The closing
# escape is deliberately outside the URL capture; otherwise it would become a
# literal trailing backslash in the Markdown destination.
DRAFT_AUTOLINK_RE = re.compile(
    r"\\?<(?P<url>https?://(?:[^<>\\\s]|\\(?!>))+?)\\?>"
)
ESCAPED_URL_CHARACTER_RE = re.compile(r"\\([!\"#$%&'()*+,./:;<=>?@\[\]^_`{|}~-])")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def slugify(value: str) -> str:
    value = value.translate(CYRILLIC).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def source_metadata(source_root: Path, source: Path) -> dict[str, object]:
    relative = source.relative_to(source_root)
    stem = source.stem
    section = None
    title = stem
    match = SECTION_RE.match(stem)
    if match:
        section = match.group("section").rstrip(".")
        title = match.group("title")

    relative_stem = relative.with_suffix("").as_posix()
    slug = slugify(relative_stem)
    document_type = "chapter"
    if relative.parts[0] == "Врезки":
        document_type = "sidebar"
    elif "Шаблон" in title or "бланк" in title.lower():
        document_type = "template"
    elif "SRD" in title:
        document_type = "srd"
    elif "Внешние ссылки" in title:
        document_type = "reference"

    return {
        "id": f"ouw25-{slug}",
        "slug": slug,
        "title": title,
        "section": section,
        "document_type": document_type,
        "source_path": source.relative_to(source_root.parent).as_posix(),
        "source_sha256": sha256(source),
    }


def pandoc_version(pandoc: str) -> str:
    completed = subprocess.run(
        [pandoc, "--version"], check=True, text=True, capture_output=True
    )
    return completed.stdout.splitlines()[0]


def make_relative(path: str, markdown_dir: Path, assets_root: Path) -> str:
    """Return a stable relative path when Pandoc emitted an extracted asset."""
    candidate = Path(path)
    if not candidate.is_absolute():
        return path
    try:
        candidate.relative_to(assets_root.resolve())
    except ValueError:
        return path
    return os.path.relpath(candidate, markdown_dir).replace(os.sep, "/")


def localize_media_paths(text: str, markdown_dir: Path, assets_root: Path) -> str:
    def html_replacer(match: re.Match[str]) -> str:
        original = match.group(0)
        relative = make_relative(match.group("path"), markdown_dir, assets_root)
        return original.replace(match.group("path"), relative)

    def markdown_replacer(match: re.Match[str]) -> str:
        relative = make_relative(match.group("path"), markdown_dir, assets_root)
        return f"{match.group('prefix')}{relative}{match.group('suffix')}"

    return MD_IMAGE_RE.sub(markdown_replacer, HTML_IMAGE_RE.sub(html_replacer, text))


def compact_form_fields(text: str) -> tuple[str, int]:
    """Replace long blank underlines with a compact, indexable form marker."""
    result: list[str] = []
    pending_blank = False
    previous_was_field = False
    replaced = 0

    for line in text.splitlines():
        underscore_count = line.count(r"\_")
        if underscore_count >= 10:
            prefix_match = re.match(r"^(\s*(?:[-*+]\s+)?)", line)
            field = f"{prefix_match.group(1)}[Поле для заполнения]"
            replaced += 1
            if previous_was_field:
                pending_blank = False
                continue
            if pending_blank:
                result.append("")
                pending_blank = False
            result.append(field)
            previous_was_field = True
            continue
        if not line.strip() and previous_was_field:
            pending_blank = True
            continue
        if pending_blank:
            result.append("")
            pending_blank = False
        result.append(line.rstrip())
        previous_was_field = False

    if pending_blank:
        result.append("")
    return "\n".join(result).strip() + "\n", replaced


def normalize_links(text: str) -> tuple[str, int]:
    """Turn DOCX/Pandoc draft links into portable Markdown link syntax."""
    replacements = 0

    def clean_url(value: str) -> str:
        return ESCAPED_URL_CHARACTER_RE.sub(r"\1", value)

    def escaped_link_replacer(match: re.Match[str]) -> str:
        nonlocal replacements
        replacements += 1
        return f"[{match.group('label')}]({clean_url(match.group('url'))})"

    def open_link_replacer(match: re.Match[str]) -> str:
        nonlocal replacements
        replacements += 1
        link = match.group("link")
        return re.sub(
            r"\((?P<url>[^)]+)\)$",
            lambda destination: f"({clean_url(destination.group('url'))})",
            link,
        )

    def autolink_replacer(match: re.Match[str]) -> str:
        nonlocal replacements
        replacements += 1
        url = clean_url(match.group("url"))
        return f"[{url}]({url})"

    text = ESCAPED_LINK_RE.sub(escaped_link_replacer, text)
    text = DRAFT_OPEN_LINK_RE.sub(open_link_replacer, text)
    text = DRAFT_AUTOLINK_RE.sub(autolink_replacer, text)
    return text, replacements


def normalize_markdown(text: str) -> tuple[str, dict[str, int]]:
    """Apply only structural transformations that do not alter prose."""
    stats = {
        "form_fields_compacted": 0,
        "images": 0,
        "heading_levels_shifted": 0,
        "links_normalized": 0,
    }

    text = text.replace("\r\n", "\n")
    text = re.sub(r"</?u>", "", text, flags=re.I)
    text, stats["links_normalized"] = normalize_links(text)
    text = ILLUSTRATION_RE.sub(
        lambda match: f"> **{match.group('description').strip()}**", text
    )

    def image_replacer(match: re.Match[str]) -> str:
        stats["images"] += 1
        return f"![Изображение — требуется описание]({match.group('path')})\n"

    text = HTML_IMAGE_RE.sub(image_replacer, text)
    text, replaced = compact_form_fields(text)
    stats["form_fields_compacted"] = replaced
    text = re.sub(
        r"^#{1,6}\s+\[Поле для заполнения\]\s*$",
        "[Поле для заполнения]",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(r"^#{1,6}\s+(?=!\[Изображение)", "", text, flags=re.MULTILINE)

    headings = list(HEADING_RE.finditer(text))
    if headings:
        minimum_level = min(len(match.group("hashes")) for match in headings)
        previous_level = 1

        def heading_replacer(match: re.Match[str]) -> str:
            nonlocal previous_level
            source_level = len(match.group("hashes"))
            target_level = min(6, source_level - minimum_level + 2)
            # DOCX visual styles often jump from, for example, Heading 3 to
            # Heading 5. Markdown heading paths used by chunkers must not have
            # such gaps, so cap an increase at one level at a time.
            target_level = min(target_level, previous_level + 1)
            if target_level != source_level:
                stats["heading_levels_shifted"] += 1
            previous_level = target_level
            return f"{'#' * target_level} {match.group('title')}"

        text = HEADING_RE.sub(heading_replacer, text)

    text = re.sub(
        r"^(#{1,6}\s+.+)\n(?!\n)", r"\1\n\n", text, flags=re.MULTILINE
    )
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return text, stats


def front_matter(metadata: dict[str, object], has_media: bool, pandoc: str) -> str:
    values = [
        ("id", metadata["id"]),
        ("title", metadata["title"]),
        ("source_path", metadata["source_path"]),
        ("source_sha256", metadata["source_sha256"]),
        ("document_type", metadata["document_type"]),
        ("section", metadata["section"]),
        ("language", "ru"),
        ("license", "Public Domain"),
        ("license_scope", "text"),
        ("asset_license", "UNSPECIFIED"),
        ("status", "needs_review"),
        ("tags", []),
        ("aliases", []),
        ("has_media", has_media),
        ("converted_with", pandoc),
    ]
    lines = ["---"]
    for key, value in values:
        if isinstance(value, str):
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
        elif value is None:
            lines.append(f"{key}: null")
        else:
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    return "\n".join(lines) + "\n---\n\n"


def run_pandoc(pandoc: str, source: Path, asset_dir: Path) -> str:
    asset_dir.mkdir(parents=True, exist_ok=True)
    command = [
        pandoc,
        str(source),
        "--from=docx",
        "--to=gfm",
        "--wrap=none",
        f"--extract-media={asset_dir}",
    ]
    completed = subprocess.run(command, check=True, text=True, capture_output=True)
    return completed.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--pandoc", default="pandoc")
    parser.add_argument(
        "--refresh-markdown",
        action="store_true",
        help="Overwrite normalized Markdown files; use only before manual review.",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    source_root = root / "docx_sources"
    content_root = root / "content"
    imported_root = content_root / "imported"
    markdown_root = content_root / "markdown"
    assets_root = content_root / "assets"
    manifests_root = content_root / "manifests"
    for directory in (imported_root, markdown_root, assets_root, manifests_root):
        directory.mkdir(parents=True, exist_ok=True)

    if not source_root.is_dir():
        parser.error(f"source directory not found: {source_root}")
    try:
        version = pandoc_version(args.pandoc)
    except (OSError, subprocess.CalledProcessError) as error:
        parser.error(f"Pandoc is unavailable: {error}")

    documents: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []
    sources = sorted(source_root.rglob("*.docx"), key=lambda path: path.as_posix())
    for source in sources:
        metadata = source_metadata(source_root, source)
        slug = str(metadata["slug"])
        asset_dir = assets_root / slug
        imported_path = imported_root / f"{slug}.md"
        markdown_path = markdown_root / f"{slug}.md"

        # The directory belongs to this deterministic document slug. Removing it
        # prevents obsolete image files after a source DOCX is replaced.
        if asset_dir.exists():
            shutil.rmtree(asset_dir)
        raw = run_pandoc(args.pandoc, source, asset_dir)
        raw = localize_media_paths(raw, imported_path.parent, assets_root)
        imported_path.write_text(raw.rstrip() + "\n", encoding="utf-8")

        normalized, stats = normalize_markdown(raw)
        normalized = localize_media_paths(normalized, markdown_path.parent, assets_root)
        has_media = bool(list(asset_dir.rglob("*")))
        if args.refresh_markdown or not markdown_path.exists():
            body = f"# {metadata['title']}\n\n{normalized}"
            markdown_path.write_text(
                front_matter(metadata, has_media, version) + body,
                encoding="utf-8",
            )

        record = {
            **metadata,
            "imported_path": imported_path.relative_to(root).as_posix(),
            "markdown_path": markdown_path.relative_to(root).as_posix(),
            "asset_path": asset_dir.relative_to(root).as_posix(),
            "has_media": has_media,
            "pandoc": version,
            "normalization": stats,
            "status": "needs_review",
        }
        documents.append(record)
        if has_media:
            issues.append(
                {
                    "document_id": metadata["id"],
                    "category": "image_description",
                    "severity": "review",
                    "status": "open",
                    "message": "Добавить содержательные описания к изображениям перед визуальным поиском.",
                }
            )
        if stats["form_fields_compacted"]:
            issues.append(
                {
                    "document_id": metadata["id"],
                    "category": "template_fields",
                    "severity": "review",
                    "status": "open",
                    "message": "Пустые строки бланка свёрнуты в маркеры «Поле для заполнения»; сверить форму с DOCX.",
                }
            )

    manifest = {
        "schema_version": 1,
        "generated_at": dt.date.today().isoformat(),
        "source_directory": "docx_sources",
        "pandoc": version,
        "documents": documents,
    }
    (manifests_root / "documents.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (manifests_root / "issues.json").write_text(
        json.dumps({"schema_version": 1, "issues": issues}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(f"Converted {len(documents)} DOCX files with {version}.")
    print(f"Normalized Markdown: {markdown_root.relative_to(root)}")
    print(f"Open review items: {len(issues)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
