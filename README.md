# 🧠 MindPixel — Erasmus+ Training Course Toolkit

[![Deploy to GitHub Pages](https://github.com/kokorikos212/MindPixel/actions/workflows/deploy.yml/badge.svg)](https://github.com/kokorikos212/MindPixel/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**MindPixel** is a practical, open-source toolkit for youth workers, trainers, and educators — born out of an Erasmus+ Training Course held in **Bansko, Bulgaria** (July 2–12, 2026).

We explore the intersection of **digital safety, data protection, artificial intelligence, and youth mental wellbeing** — not through lectures, but through **creative, arts-based methods**. Art, games, poetry, and reflection become tools for understanding how technology shapes young people's lives.

> 🌐 **Live site:** [kokorikos212.github.io/MindPixel/search.html](https://kokorikos212.github.io/MindPixel/search.html)

---

## ✨ Features

### 🔍 Natural Language Semantic Search
Describe what you need in plain English and the toolkit finds the most relevant activity:

> *"a quick outdoor energizer for 20 people with no materials"*
> → returns Attack & Dodge (92% match)

> *"workshop about emotions and self-reflection through art"*
> → returns Two Hands, Two Selves (89% match)

Powered by **Transformers.js** — the embedding model runs entirely in your browser. No server, no API keys, no tracking.

### 📋 Structured Activity Metadata
Every game and workshop is tagged with searchable fields:

| Field | Example | What it means |
|-------|---------|--------------|
| `type` | `game`, `workshop`, `day-log` | Kind of content |
| `duration` | `10`, `30`, `90` | Time needed (minutes) |
| `group_size` | `6-30`, `10-25` | How many participants |
| `materials` | `none`, `paper, pens` | What you need |
| `location` | `indoor`, `outdoor`, `both` | Where it works |
| `energy` | `low`, `medium`, `high` | Activity intensity |

### 🖥️ GitHub Pages Site
The vault is automatically built into a browsable static website with:
- Clean, readable typography (light + dark mode)
- Wiki-link navigation between pages
- Obsidian-style callout blocks (`> [!tip]`, `> [!quote]`)
- Metadata pills on every page
- Clickable tags that pre-fill the search

---

## 📂 Project Structure

```
Verse/
├── 1.Welcome to MindPixel.md          # Introduction
├── 2. Table of contents.md            # Vault index
├── 3.How to Use This Toolkit.md       # Usage guide
├── Participants.md                    # People involved
├── search.html                        # 🔍 Semantic search UI
│
├── Games/                             # 10 group games & energizers
│   ├── Ninja.md
│   ├── Zombie.md
│   ├── Name Ball.md
│   └── ...
│
├── Workshops/                         # 10 creative workshops
│   ├── Two Hands, Two Selves.md
│   ├── Guess Who?.md
│   ├── Befriending shame.md
│   └── ...
│
├── Days/                              # 8 daily session logs
│   ├── 01. Day 1 — Common Ground & Connections.md
│   └── ...
│
├── tools/                             # Build system
│   ├── build_index.py                 # Generates embeddings
│   ├── build_site.py                  # Converts .md → .html
│   └── requirements.txt
│
├── templates/
│   └── page.html                      # HTML template for notes
│
└── .github/workflows/
    └── deploy.yml                     # Auto-deploy to GitHub Pages
```

---

## 🚀 Quick Start

### Browse in Obsidian
Clone the repo and open the `Verse/` folder as an Obsidian vault. All wiki links, tags, and callouts work natively.

```bash
git clone https://github.com/kokorikos212/MindPixel.git
# Open MindPixel/Verse in Obsidian
```

### Build the static site locally

```bash
cd MindPixel/Verse
pip install -r tools/requirements.txt

# Generate the semantic search index (embeddings)
python3 tools/build_index.py

# Convert all .md files to .html
python3 tools/build_site.py

# Serve locally
cd _site && python3 -m http.server 8080
# Open http://localhost:8080/search.html
```

### Deploy to GitHub Pages
The repo includes a GitHub Actions workflow that builds and deploys automatically on every push to `main`. To enable it:

1. Go to **Settings → Pages**
2. Set **Source** to **GitHub Actions**
3. Push to `main` — the site deploys in ~3 minutes

---

## 🔧 How the Search Works

```
User types natural language query
          ↓
Transformers.js loads all-MiniLM-L6-v2 (in your browser, ~30 MB cached)
          ↓
Query is embedded to a 384-dimensional vector
          ↓
Cosine similarity scored against 33 pre-computed file embeddings
          ↓
Top-12 results shown with metadata, snippets, and links
```

The embedding model runs **client-side only** — your search queries never leave your browser. The pre-computed index (`search-index.json`) is generated at build time by `tools/build_index.py`.

---

## 📝 Adding New Content

1. Create a new `.md` file in the appropriate folder (`Games/`, `Workshops/`, `Days/`)
2. Add YAML frontmatter at the top:

```yaml
---
tags:
  - your-tag
  - another-tag
type: game          # game | workshop | day-log | hub | page
duration: 20        # minutes (number)
group_size: 5-25    # participant range
materials: none     # or comma-separated list
location: both      # indoor | outdoor | both
energy: medium      # low | medium | high
---
```

3. Write your content using standard Markdown + Obsidian syntax (`[[wiki links]]`, `> [!callout]`)
4. Push to `main` — GitHub Actions rebuilds the search index and deploys automatically

---

## 🎯 Use Cases

| You want to… | How the toolkit helps |
|-------------|---------------------|
| Find a 10-minute energizer for 30 people | Type it in the search bar |
| Plan a workshop about digital privacy | Search + filter by `type: workshop` |
| See what happened on Day 4 | Browse `Days/` or search by day |
| Adapt an activity for outdoors | Filter by `location: outdoor` |
| Use the toolkit in your own training | Clone, remix, and redeploy |

---

## 🤝 Contributing

This is an open-source resource. If you use these activities and adapt them, we'd love to hear about it. Open an issue or pull request with your variations, translations, or new activities.

---

## 📄 License

This project is licensed under the MIT License — you're free to use, modify, and share it.

---

*MindPixel was made possible by Erasmus+ and an international team of youth workers, educators, and artists who believed that art can say what lectures cannot.*
