#!/usr/bin/env python3
"""
Convert the MindPixel vault to a static HTML site.

- Resolves Obsidian [[wiki-links]] to proper relative URLs.
- Converts > [!callout] blocks to styled <aside> elements.
- Wraps every page in a shared Jinja2 template.
- Writes everything into _site/ ready for GitHub Pages.
"""

import json
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, Optional

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader

# --- paths ---
VAULT_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = VAULT_DIR / "templates"
OUTPUT_DIR = VAULT_DIR / "_site"

SKIP_DIRS = {".git", "_site", "tools", "templates", ".github", "node_modules", "__pycache__"}
SKIP_FILES = {"search.html"}  # hand-crafted files we don't overwrite


# ---------------------------------------------------------------------------
# wiki-link resolver
# ---------------------------------------------------------------------------

def build_name_index(vault_dir: Path) -> Dict[str, str]:
    """
    Scan every .md file and map its *page name* (stem) → relative html path.

    Because Obsidian wiki-links match by file name (no extension), we need
    to know which directory each name lives in.
    """
    index: Dict[str, str] = {}
    for md_path in sorted(vault_dir.rglob("*.md")):
        if any(d in md_path.parts for d in SKIP_DIRS):
            continue
        rel = md_path.relative_to(vault_dir)
        html_rel = str(rel.with_suffix(".html"))
        name = rel.stem  # filename without .md
        index[name] = html_rel
    return index


def resolve_wiki_links(text: str, name_index: Dict[str, str],
                       current_rel: str) -> str:
    """
    Replace [[Target]] and [[Target|alias]] with <a href="…">…</a>.

    If the target cannot be found in *name_index* we still generate a link
    (the user may add the page later) but add a `class="missing"` so it
    can be styled differently.
    """
    current_dir = Path(current_rel).parent

    def _replace(m: re.Match) -> str:
        target = m.group(1).strip()
        anchor = ""
        # split on | for alias
        if "|" in target:
            target, alias = target.split("|", 1)
            target, alias = target.strip(), alias.strip()
        elif "#" in target:
            # link to a heading inside a page
            target, anchor = target.split("#", 1)
            target, anchor = target.strip(), anchor.strip().replace(" ", "-").lower()
            alias = f"{target} › {anchor}"
        else:
            alias = target.strip()

        # look up the file
        if target in name_index:
            href = name_index[target]
            # make relative from current file
            try:
                href = str(Path(href).relative_to(current_dir))
            except ValueError:
                pass
            if anchor:
                href += f"#{anchor}"
            return f'<a href="{href}">{alias}</a>'
        else:
            # unresolved link – keep visible but mark as missing
            return f'<a href="#" class="missing" title="page not found: {target}">{alias}</a>'

    # [[Target]] or [[Target|alias]] or [[Target#heading]]
    return re.sub(r"\[\[([^\]]+)\]\]", _replace, text)


# ---------------------------------------------------------------------------
# callout converter
# ---------------------------------------------------------------------------

def convert_callouts(text: str) -> str:
    """
    Turn Obsidian callouts into HTML <aside> blocks.

    Input:
        > [!note] Title
        > Body line 1
        > Body line 2

    Output:
        <aside class="callout callout-note">
        <p class="callout-title">Title</p>
        <p>Body line 1</p>
        <p>Body line 2</p>
        </aside>
    """
    lines = text.split("\n")
    out: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        m = re.match(r"^>\s*\[!(\w+)\]\s*(.*)", line)
        if m:
            callout_type = m.group(1).lower()
            title = m.group(2).strip()

            out.append(f'<aside class="callout callout-{callout_type}">')
            if title:
                out.append(f'<p class="callout-title">{title}</p>')

            i += 1
            # consume continuation lines
            while i < len(lines) and lines[i].startswith(">"):
                body = lines[i][1:]  # strip leading >
                if body.startswith(" "):
                    body = body[1:]
                out.append(body)
                i += 1
            out.append("</aside>")
        else:
            out.append(line)
            i += 1

    return "\n".join(out)


# ---------------------------------------------------------------------------
# html rendering
# ---------------------------------------------------------------------------

def render_page(md_text: str, meta: dict, rel_path: str,
                name_index: Dict[str, str]) -> str:
    """Convert a single .md source string to a full HTML page."""

    # resolve wiki links first (before markdown conversion)
    text = resolve_wiki_links(md_text, name_index, rel_path)
    # convert callouts
    text = convert_callouts(text)

    # strip the first H1 heading (it's already in the template)
    text = re.sub(r"^#\s+.+(\n|$)", "", text, count=1).strip()

    # compute directory depth for relative asset paths
    depth = rel_path.count("/")
    prefix = "../" * depth if depth > 0 else ""

    # standard markdown → html
    html_body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "codehilite", "toc"],
    )

    # fix relative asset paths for subdirectory pages
    if prefix:
        html_body = html_body.replace('src="assets/', f'src="{prefix}assets/')

    # wrap leading images in a gallery div for horizontal scrolling
    # markdown puts consecutive images in one <p> as: <p><img...><img...></p>
    html_body = re.sub(
        r'^(<p>(<img[^>]+>\s*)+</p>\s*)+',
        lambda m: f'<div class="slide-gallery">{m.group(0)}</div>',
        html_body,
        count=1,
    )

    # render into template
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("page.html")

    # normalise tags
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]

    return template.render(
        title=meta.get("title", ""),
        type=meta.get("type", ""),
        duration=meta.get("duration", ""),
        group_size=meta.get("group_size", ""),
        materials=meta.get("materials", ""),
        location=meta.get("location", ""),
        energy=meta.get("energy", ""),
        tags=tags,
        content=html_body,
        path=rel_path,
    )


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    print("▸ Building name index …")
    name_index = build_name_index(VAULT_DIR)

    # clean output dir but keep hand-crafted files
    OUTPUT_DIR.mkdir(exist_ok=True)

    file_count = 0

    for md_path in sorted(VAULT_DIR.rglob("*.md")):
        if any(d in md_path.parts for d in SKIP_DIRS):
            continue

        rel = str(md_path.relative_to(VAULT_DIR))
        raw = md_path.read_text(encoding="utf-8")

        # split frontmatter
        meta, body = {}, raw
        if raw.startswith("---"):
            parts = raw.split("---", 2)
            if len(parts) >= 3:
                try:
                    meta = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError:
                    pass
                body = parts[2]

        # add title from first heading, or fall back to filename
        if "title" not in meta:
            m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
            if m:
                meta["title"] = m.group(1).strip()
            else:
                # fallback: clean up filename
                name = md_path.stem
                name = re.sub(r"^\d+\.\s*", "", name)
                meta["title"] = name

        html = render_page(body, meta, rel, name_index)

        # write
        out_path = OUTPUT_DIR / rel.replace(".md", ".html")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        file_count += 1

    print(f"✔  {file_count} HTML pages written to {OUTPUT_DIR}")

    # copy search.html if it exists at vault root
    search_src = VAULT_DIR / "search.html"
    if search_src.exists():
        shutil.copy2(search_src, OUTPUT_DIR / "search.html")
        print("✔  search.html copied")

    # copy pre-computed search index (may not exist in CI — that's ok)
    index_src = VAULT_DIR / "search-index.json"
    if index_src.exists():
        shutil.copy2(index_src, OUTPUT_DIR / "search-index.json")
        print("✔  search-index.json copied")

    # copy assets folder (slides, images)
    assets_src = VAULT_DIR / "assets"
    if assets_src.is_dir():
        assets_dst = OUTPUT_DIR / "assets"
        if assets_dst.exists():
            shutil.rmtree(assets_dst)
        shutil.copytree(assets_src, assets_dst)
        print("✔  assets/ copied")

    print("Done.")


if __name__ == "__main__":
    main()
