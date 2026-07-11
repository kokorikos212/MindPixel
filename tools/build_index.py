#!/usr/bin/env python3
"""
Build search index with embeddings for the MindPixel vault.

Reads all markdown files, extracts frontmatter and body text,
generates embeddings using all-MiniLM-L6-v2, and writes
a search-index.json that powers the client-side semantic search.
"""

import json
import re
import sys
from pathlib import Path

import yaml
from sentence_transformers import SentenceTransformer

# --- paths ---
VAULT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = VAULT_DIR / "_site"
OUTPUT_DIR.mkdir(exist_ok=True)

# files / dirs to skip
SKIP_PATTERNS = {".git", "_site", "tools", "templates", ".github", "node_modules"}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Pull YAML frontmatter and body apart.  Returns (meta, body)."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        meta = {}
    return meta, parts[2].strip()


def extract_title(body: str, filepath: Path) -> str:
    """Return the first H1 or a cleaned-up filename."""
    m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    if m:
        return m.group(1).strip()
    # fallback – strip leading numbers and dots
    name = filepath.stem
    name = re.sub(r"^\d+\.\s*", "", name)
    return name


def make_snippet(text: str, max_chars: int = 220) -> str:
    """Strip markdown noise and return a short plain-text preview."""
    # resolve wiki links → keep display text or target
    clean = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", text)
    # drop common md syntax
    clean = re.sub(r"[#*>`\-|_~]", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    if len(clean) <= max_chars:
        return clean
    return clean[:max_chars].rsplit(" ", 1)[0] + "…"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    print("▸ Loading embedding model (all-MiniLM-L6-v2) …")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    records: list[dict] = []
    texts: list[str] = []

    # collect every markdown file -------------------------------------------
    for md_path in sorted(VAULT_DIR.rglob("*.md")):
        if any(part in SKIP_PATTERNS for part in md_path.parts):
            continue

        rel = str(md_path.relative_to(VAULT_DIR))
        raw = md_path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)

        title = extract_title(body, md_path)
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]

        # build a rich searchable text blob
        search_text = f"{title}\n{' '.join(tags)}\n{body}"

        records.append({
            "path": rel,
            "title": title,
            "type": meta.get("type", ""),
            "duration": meta.get("duration", ""),
            "group_size": meta.get("group_size", ""),
            "materials": meta.get("materials", ""),
            "location": meta.get("location", ""),
            "energy": meta.get("energy", ""),
            "tags": tags,
            "snippet": make_snippet(body),
        })
        texts.append(search_text)

    print(f"▸ Generating embeddings for {len(records)} files …")
    embeddings = model.encode(texts, show_progress_bar=True)

    for i, vec in enumerate(embeddings):
        records[i]["embedding"] = vec.tolist()

    # write combined index --------------------------------------------------
    index_path = OUTPUT_DIR / "search-index.json"
    index_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    size_mb = index_path.stat().st_size / (1024 * 1024)
    print(f"✔  search-index.json  ({len(records)} entries, {size_mb:.1f} MB)")

    # also write a lightweight metadata file (no vectors) for browsing -----
    meta_only = [{k: v for k, v in r.items() if k != "embedding"} for r in records]
    meta_path = OUTPUT_DIR / "metadata.json"
    meta_path.write_text(
        json.dumps(meta_only, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"✔  metadata.json")

    print("Done.")


if __name__ == "__main__":
    main()
