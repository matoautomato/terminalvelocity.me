# terminalvelocity.me

Personal / professional website. Static HTML, Tailwind CSS, vanilla JS. No frameworks.

## Stack

- **HTML/CSS**: Static pages assembled from components via `build.py`
- **Tailwind CSS v3.4**: Compiled to `assets/styles.css`
- **JavaScript**: Vanilla only (typewriter animations, language toggle, glow effect)
- **Python**: Page assembly (`build.py`) and blog publishing (`publish.py`)

## Development

```bash
npm install
npm run dev      # build + local server on :8000
npm run build    # tailwind compile + page assembly
```

## Blog Publishing

Posts are written in Markdown with YAML frontmatter and converted to static HTML via `publish.py` — a zero-dependency Python script.

```bash
python3 publish.py path/to/post.md          # publish a post
python3 publish.py --dry-run                 # preview without writing
python3 publish.py --rss                     # regenerate RSS feed
python3 publish.py --rebuild-all             # rebuild all posts
```

A post looks like this:

```markdown
---
title: Your Post Title
slug: your-post-slug
date: 2026-04-05
excerpt: Short description for cards and RSS.
---

Content here.
```

Publishing auto-generates the post page, updates the blog index, homepage, post navigation, and RSS feed.

## Blog Migration

The blog will be migrated to [Hugo](https://gohugo.io/) for easier content management.
