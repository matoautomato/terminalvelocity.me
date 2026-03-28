#!/usr/bin/env python3
"""
publish.py — Markdown → HTML blog post generator for terminalvelocity.me

Usage:
    python3 publish.py blog/drafts/my-post.md
    python3 publish.py blog/drafts/my-post.md --dry-run

Frontmatter format (YAML-like, between --- fences):
    ---
    title: Your Post Title
    subtitle: A witty one-liner
    slug: your-post-slug
    date: 2026-03-22
    image: /assets/optional-image.webp
    image_alt: Description of the image
    read_time: 5 min read
    excerpt: Short teaser for the blog landing page card.
    ---

    Your markdown content here...

Supported Markdown:
    ## Headings (h2 only — h1 is the title)
    **bold**, *italic*, `inline code`
    [links](url)
    ![images](url)
    > blockquotes
    - unordered lists
    Paragraphs (separated by blank lines)
    --- (horizontal rules, only between paragraphs)

What it does:
    1. Parses frontmatter + markdown from the draft file
    2. Generates blog/slug/index.html from the post template
    3. Rebuilds blog/index.html (landing page) with all posts
    4. Updates the Writing tab cards on the main index.html
    5. Reports what changed
"""

import sys
import os
import re
import html
import json
from pathlib import Path
from datetime import datetime

SITE_ROOT = Path(__file__).parent.resolve()
BLOG_DIR = SITE_ROOT / "blog"
DRAFTS_DIR = BLOG_DIR / "drafts"
COMPONENTS_DIR = SITE_ROOT / "components"
PAGES_DIR = SITE_ROOT / "pages"
SITE_URL = "https://terminalvelocity.me"


from build import load_component, NAV_CTA_BOOKING_DESKTOP, NAV_CTA_BOOKING_MOBILE


# ---------------------------------------------------------------------------
# Frontmatter parser (zero-dependency, handles simple key: value YAML)
# ---------------------------------------------------------------------------
def parse_frontmatter(text):
    """Parse --- delimited frontmatter and return (metadata_dict, body_text)."""
    if not text.startswith("---"):
        print("ERROR: File must start with --- frontmatter fence")
        sys.exit(1)

    parts = text.split("---", 2)
    if len(parts) < 3:
        print("ERROR: Missing closing --- frontmatter fence")
        sys.exit(1)

    raw_meta = parts[1].strip()
    body = parts[2].strip()

    meta = {}
    for line in raw_meta.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        # Strip surrounding quotes
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        meta[key] = value

    # Validate required fields
    required = ["title", "slug", "date"]
    missing = [f for f in required if f not in meta]
    if missing:
        print(f"ERROR: Missing required frontmatter fields: {', '.join(missing)}")
        sys.exit(1)

    return meta, body


# ---------------------------------------------------------------------------
# Minimal Markdown → HTML converter
# ---------------------------------------------------------------------------
def md_to_html(md_text):
    """Convert markdown text to HTML paragraphs. Minimal, no dependencies."""
    lines = md_text.split("\n")
    html_blocks = []
    current_block = []
    in_list = False
    list_items = []

    def flush_paragraph():
        if current_block:
            text = " ".join(current_block)
            text = inline_format(text)
            html_blocks.append(f'    <p class="mb-4">{text}</p>')
            current_block.clear()

    def flush_list():
        nonlocal in_list
        if list_items:
            items = "\n".join(f"      <li>{inline_format(li)}</li>" for li in list_items)
            html_blocks.append(f'    <ul class="list-disc list-inside mb-4 space-y-1">\n{items}\n    </ul>')
            list_items.clear()
        in_list = False

    def inline_format(text):
        # Smart quotes (before any HTML generation to avoid mangling attributes)
        text = re.sub(r'"([^"]*)"', r'&ldquo;\1&rdquo;', text)
        # Em dash
        text = text.replace(" --- ", " &mdash; ").replace(" -- ", " &mdash; ")
        # Images: ![alt](src)
        text = re.sub(
            r'!\[([^\]]*)\]\(([^)]+)\)',
            r'</p>\n    <img src="\2" alt="\1" class="w-full max-w-lg my-6 rounded-sm"/>\n    <p class="mb-4">',
            text
        )
        # Links: [text](url)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" class="text-primary hover:text-secondary-accent underline" target="_blank" rel="noopener noreferrer">\1</a>', text)
        # Bold: **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Italic: *text* (but not inside ** pairs)
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
        # Inline code: `text`
        text = re.sub(r'`([^`]+)`', r'<code class="bg-surface-container px-1.5 py-0.5 rounded-sm text-xs">\1</code>', text)
        return text

    for line in lines:
        stripped = line.strip()

        # Horizontal rule
        if stripped == "---" or stripped == "***" or stripped == "___":
            flush_paragraph()
            flush_list()
            html_blocks.append('    <hr class="border-outline-variant/30 my-8"/>')
            continue

        # Heading (## only, h1 is the post title)
        heading_match = re.match(r'^(#{2,6})\s+(.+)$', stripped)
        if heading_match:
            flush_paragraph()
            flush_list()
            level = len(heading_match.group(1))
            text = inline_format(heading_match.group(2))
            size_class = {2: "text-xl", 3: "text-lg", 4: "text-base", 5: "text-sm", 6: "text-xs"}
            html_blocks.append(f'    <h{level} class="font-bold {size_class.get(level, "text-base")} mt-8 mb-4">{text}</h{level}>')
            continue

        # Blockquote
        if stripped.startswith("> "):
            flush_paragraph()
            flush_list()
            text = inline_format(stripped[2:])
            html_blocks.append(f'    <blockquote class="border-l-[3px] border-primary/50 pl-4 my-4 text-on-surface-variant italic">{text}</blockquote>')
            continue

        # Unordered list item
        list_match = re.match(r'^[-*+]\s+(.+)$', stripped)
        if list_match:
            flush_paragraph()
            if not in_list:
                in_list = True
            list_items.append(list_match.group(1))
            continue

        # Blank line
        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        # Regular text — accumulate into paragraph
        if in_list:
            flush_list()
        current_block.append(stripped)

    flush_paragraph()
    flush_list()

    result = "\n\n".join(html_blocks)
    # Clean up empty paragraphs from image handling
    result = result.replace('<p class="mb-4"></p>', '')
    return result


# ---------------------------------------------------------------------------
# HTML entity helpers
# ---------------------------------------------------------------------------

def smart_quotes(text):
    """Convert straight quotes to smart quotes in title/subtitle."""
    text = text.replace("'", "&rsquo;")
    text = re.sub(r'"([^"]*)"', r'&ldquo;\1&rdquo;', text)
    return text


# ---------------------------------------------------------------------------
# Load all published posts (for navigation + landing page)
# ---------------------------------------------------------------------------
def load_all_posts():
    """Scan blog directories and return list of post metadata, newest first."""
    posts = []
    for slug_dir in sorted(BLOG_DIR.iterdir()):
        if not slug_dir.is_dir() or slug_dir.name in ("drafts",):
            continue
        index_file = slug_dir / "index.html"
        if not index_file.exists():
            continue

        content = index_file.read_text(encoding="utf-8")

        # Extract metadata from existing HTML
        title_match = re.search(r'<h1[^>]*>(.+?)</h1>', content)
        subtitle_match = re.search(r'<p class="font-mono text-base text-on-surface-variant(?:/70)? italic mb-4">(.+?)</p>', content)
        date_match = re.search(r'<p class="font-mono text-\[10px\] uppercase tracking-widest text-on-surface-variant">(\d{4}-\d{2}-\d{2})</p>', content)
        read_time_match = re.search(r'<p class="font-mono text-xs text-on-surface-variant mb-8">(.+?)</p>', content)

        # Extract first paragraph for excerpt
        excerpt_match = re.search(r'<div class="font-body text-sm text-on-surface-variant leading-relaxed">\s*<p class="mb-4">(.+?)</p>', content, re.DOTALL)

        # Extract og:image for RSS feed
        og_image_match = re.search(r'<meta property="og:image" content="([^"]+)"', content)

        # Extract full article content div for RSS feed
        content_div_match = re.search(
            r'<div class="font-body text-sm text-on-surface-variant leading-relaxed">(.*?)\s*</div>\s*</div>\s*(?:<!-- Post navigation)',
            content, re.DOTALL
        )

        if title_match and date_match:
            posts.append({
                "slug": slug_dir.name,
                "title": title_match.group(1).strip(),
                "subtitle": subtitle_match.group(1).strip() if subtitle_match else "",
                "date": date_match.group(1),
                "read_time": read_time_match.group(1) if read_time_match else "",
                "excerpt": excerpt_match.group(1).strip() if excerpt_match else "",
                "og_image": og_image_match.group(1) if og_image_match else "",
                "content_html": content_div_match.group(1).strip() if content_div_match else "",
            })

    # Sort by date descending
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


# ---------------------------------------------------------------------------
# Generate blog post HTML
# ---------------------------------------------------------------------------
def generate_post_html(meta, content_html, prev_post=None, next_post=None):
    """Generate full blog post HTML page using shared components."""
    title = smart_quotes(meta["title"])
    subtitle = smart_quotes(meta.get("subtitle", ""))
    date = meta["date"]
    read_time = meta.get("read_time", estimate_read_time(content_html))

    # Build post navigation
    nav_prev = ""
    if prev_post:
        nav_prev = f'''  <a href="/blog/{prev_post['slug']}/" class="bg-surface border border-outline-variant/20 border-l-[3px] border-l-transparent hover:border-l-secondary-accent rounded-sm px-4 py-3 font-mono text-sm group no-underline">
    <span class="text-on-surface-variant text-xs">&larr; previous</span><br>
    <span class="text-on-surface-variant group-hover:text-secondary-accent transition-colors">{truncate(prev_post['title'], 50)}</span>
  </a>'''
    else:
        nav_prev = '  <div class="px-4 py-3"></div>'

    nav_next = ""
    if next_post:
        nav_next = f'''  <a href="/blog/{next_post['slug']}/" class="bg-surface border border-outline-variant/20 border-l-[3px] border-l-transparent hover:border-l-secondary-accent rounded-sm px-4 py-3 font-mono text-sm group no-underline text-right">
    <span class="text-on-surface-variant text-xs">next &rarr;</span><br>
    <span class="text-on-surface-variant group-hover:text-secondary-accent transition-colors">{truncate(next_post['title'], 50)}</span>
  </a>'''
    else:
        nav_next = '  <div class="px-4 py-3"></div>'

    subtitle_html = ""
    if subtitle:
        subtitle_html = f'\n  <p class="font-mono text-base text-on-surface-variant/70 italic mb-4">{subtitle}</p>'

    og_image = meta.get("image", "/assets/og-card.png")
    og_description = html.unescape(re.sub(r'<[^>]+>', '', meta.get("excerpt", "")))[:200] or html.unescape(title)
    post_url = f"{SITE_URL}/blog/{meta['slug']}/"

    # Load shared components (raw strings, no f-string escaping needed)
    head_component = load_component("head")
    nav_component = load_component("nav")
    footer_component = load_component("footer")
    modal_component = load_component("modal")
    scripts_component = load_component("scripts")

    # Blog posts use "booking" CTA
    nav_component = nav_component.replace("<!-- NAV_CTA_DESKTOP -->", NAV_CTA_BOOKING_DESKTOP)
    nav_component = nav_component.replace("<!-- NAV_CTA_MOBILE -->", NAV_CTA_BOOKING_MOBILE)

    # Build per-post <head> meta tags
    meta_tags = f'''<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{html.unescape(title)} &mdash; matthias leyendecker_</title>
<meta name="description" content="{og_description}"/>
<meta property="og:type" content="article"/>
<meta property="og:title" content="{html.unescape(title)}"/>
<meta property="og:description" content="{og_description}"/>
<meta property="og:url" content="{post_url}"/>
<meta property="og:image" content="{SITE_URL}{og_image}"/>
<meta property="og:site_name" content="matthias leyendecker_"/>
<meta property="article:published_time" content="{date}"/>
<meta property="article:author" content="Matthias Leyendecker"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="{html.unescape(title)}"/>
<meta name="twitter:description" content="{og_description}"/>
<meta name="twitter:image" content="{SITE_URL}{og_image}"/>
<link rel="alternate" type="application/rss+xml" title="matthias leyendecker_ blog" href="{SITE_URL}/feed/index.xml"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>'''

    # Build main content area
    main_content = f'''<main class="max-w-7xl mx-auto px-4 md:px-8">
<section class="pt-32 pb-8">
<div class="bg-surface-dim/[0.92] backdrop-blur-sm rounded-sm shadow-sm border border-outline-variant/10 p-8 md:p-12 relative z-10">
  <p class="font-mono text-[10px] uppercase tracking-widest text-on-surface-variant">{date}</p>
  <h1 class="font-mono text-2xl md:text-3xl font-bold mb-2">{title}</h1>{subtitle_html}
  <p class="font-mono text-xs text-on-surface-variant mb-8">{read_time}</p>

  <div class="font-body text-sm text-on-surface-variant leading-relaxed">
{content_html}
  </div>
</div>

<!-- Post navigation -->
<div class="mt-6 flex justify-between items-stretch gap-4 relative z-10">
{nav_prev}
  <a href="/blog" class="bg-surface border border-outline-variant/20 border-l-[3px] border-l-transparent hover:border-l-secondary-accent rounded-sm px-4 py-3 font-mono text-sm group no-underline flex items-center">
    <span class="text-on-surface-variant group-hover:text-secondary-accent transition-colors">all posts</span>
  </a>
{nav_next}
</div>
</section>
</main>'''

    # Assemble full page from components
    return f'''<!DOCTYPE html>
<html class="scroll-smooth" lang="en"><head>
{meta_tags}
{head_component}
</head>
<body class="bg-surface text-on-surface font-body selection:bg-primary/20">
<div id="glow-dots"></div>
<div id="glow-overlay"></div>
{nav_component}

{main_content}

{footer_component}
{modal_component}
{scripts_component}
</body></html>'''



# ---------------------------------------------------------------------------
# Generate blog landing page
# ---------------------------------------------------------------------------
def generate_blog_landing(posts):
    """Update the blog landing template with post cards, then rebuild via build_page."""
    if not posts:
        print("WARNING: No posts found, skipping blog landing regeneration")
        return

    from build import PAGES, build_page

    hero = posts[0]
    older = posts[1:]

    hero_subtitle = ""
    if hero.get("subtitle"):
        hero_subtitle = f'\n<p class="font-mono text-sm text-on-surface-variant/70 italic mb-3">{hero["subtitle"]}</p>'

    hero_html = f'''<a href="/blog/{hero['slug']}/" class="group block bg-surface border border-outline-variant/20 border-l-[3px] border-l-transparent hover:border-l-secondary-accent rounded-sm p-8 transition-all">
<p class="font-mono text-[10px] uppercase tracking-widest text-on-surface-variant mb-3">{hero['date']}</p>
<h3 class="font-headline text-xl font-bold mb-1 group-hover:text-secondary-accent transition-colors">{hero['title']}</h3>{hero_subtitle}
<p class="font-body text-sm text-on-surface-variant leading-relaxed">{re.sub(r'<[^>]+>', '', hero.get('excerpt', ''))}</p>
</a>'''

    older_cards = []
    for post in older:
        subtitle_html = ""
        if post.get("subtitle"):
            subtitle_html = f'\n<p class="font-mono text-xs text-on-surface-variant/70 italic mb-2">{post["subtitle"]}</p>'
        older_cards.append(f'''<a href="/blog/{post['slug']}/" class="group block bg-surface border border-outline-variant/20 border-l-[3px] border-l-transparent hover:border-l-secondary-accent rounded-sm p-6 transition-all">
<p class="font-mono text-[10px] uppercase tracking-widest text-on-surface-variant mb-3">{post['date']}</p>
<h3 class="font-headline text-lg font-bold mb-1 group-hover:text-secondary-accent transition-colors">{post['title']}</h3>{subtitle_html}
<p class="font-body text-sm text-on-surface-variant leading-relaxed">{re.sub(r'<[^>]+>', '', post.get('excerpt', ''))}</p>
</a>''')

    older_grid = ""
    if older_cards:
        older_grid = f'''
<!-- Older posts grid -->
<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
{chr(10).join(older_cards)}
</div>'''

    # Update the template in pages/blog-landing.html
    template_path = PAGES_DIR / "blog-landing.html"
    existing = template_path.read_text(encoding="utf-8")
    pattern = r'(<!-- Hero post \(latest\) -->).*?(</div>\s*</section>)'
    replacement = f'''<!-- Hero post (latest) -->
{hero_html}
{older_grid}

\\2'''
    new_content = re.sub(pattern, replacement, existing, flags=re.DOTALL)
    template_path.write_text(new_content, encoding="utf-8")

    # Rebuild blog/index.html from updated template
    build_page("blog-landing", PAGES["blog-landing"])


# ---------------------------------------------------------------------------
# Update Writing tab on main index.html
# ---------------------------------------------------------------------------
def update_writing_tab(posts):
    """Update the Writing tab cards in pages/index.html template, then rebuild."""
    from build import PAGES, build_page

    template_path = PAGES_DIR / "index.html"
    if not template_path.exists():
        print("WARNING: pages/index.html not found, cannot update Writing tab")
        return

    content = template_path.read_text(encoding="utf-8")

    # Build new cards for the latest 3 posts
    latest = posts[:3]
    cards = []
    for post in latest:
        subtitle_html = ""
        if post.get("subtitle"):
            subtitle_html = f'\n<p class="font-mono text-xs text-on-surface-variant/70 italic mb-2">{post["subtitle"]}</p>'
        cards.append(f'''<a href="/blog/{post['slug']}/" class="group block bg-surface border border-outline-variant/20 border-l-[3px] border-l-transparent hover:border-l-secondary-accent rounded-sm p-6 transition-all">
<p class="font-mono text-[10px] text-on-surface-variant uppercase tracking-widest mb-2">{post['date']}</p>
<h3 class="font-headline text-lg font-bold mb-1 group-hover:text-secondary-accent transition-colors">{post['title']}</h3>{subtitle_html}
<p class="font-body text-sm text-on-surface-variant">{re.sub(r'<[^>]+>', '', post.get('excerpt', ''))}</p>
</a>''')

    # Replace post cards in the Writing tab panel
    # Match from "<!-- Post cards -->" to "<!-- View all link -->"
    pattern = r'(<!-- Post cards -->)\s*.*?\s*(<!-- View all link -->)'
    replacement = f'''\\1
{chr(10).join(cards)}
\\2'''

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if new_content != content:
        template_path.write_text(new_content, encoding="utf-8")
        # Rebuild index.html from updated template
        build_page("index", PAGES["index"])
        print(f"  Updated Writing tab in pages/index.html ({len(latest)} posts)")
    else:
        print("  Writing tab pattern not found in pages/index.html (may need manual update)")


# ---------------------------------------------------------------------------
# Update prev/next navigation on adjacent posts
# ---------------------------------------------------------------------------
def update_adjacent_nav(posts):
    """Update the prev/next navigation on posts adjacent to the new one."""
    for i, post in enumerate(posts):
        prev_post = posts[i + 1] if i + 1 < len(posts) else None
        next_post = posts[i - 1] if i > 0 else None

        post_path = BLOG_DIR / post["slug"] / "index.html"
        if not post_path.exists():
            continue

        content = post_path.read_text(encoding="utf-8")

        # Build new nav
        nav_prev = ""
        if prev_post:
            nav_prev = f'''  <a href="/blog/{prev_post['slug']}/" class="bg-surface border border-outline-variant/20 border-l-[3px] border-l-transparent hover:border-l-secondary-accent rounded-sm px-4 py-3 font-mono text-sm group no-underline">
    <span class="text-on-surface-variant text-xs">&larr; previous</span><br>
    <span class="text-on-surface-variant group-hover:text-secondary-accent transition-colors">{truncate(prev_post['title'], 50)}</span>
  </a>'''
        else:
            nav_prev = '  <div class="px-4 py-3"></div>'

        nav_next = ""
        if next_post:
            nav_next = f'''  <a href="/blog/{next_post['slug']}/" class="bg-surface border border-outline-variant/20 border-l-[3px] border-l-transparent hover:border-l-secondary-accent rounded-sm px-4 py-3 font-mono text-sm group no-underline text-right">
    <span class="text-on-surface-variant text-xs">next &rarr;</span><br>
    <span class="text-on-surface-variant group-hover:text-secondary-accent transition-colors">{truncate(next_post['title'], 50)}</span>
  </a>'''
        else:
            nav_next = '  <div class="px-4 py-3"></div>'

        # Replace the post navigation block
        nav_pattern = r'(<div class="mt-6 flex justify-between items-stretch gap-4 relative z-10">)\s*.*?\s*(</div>\s*</section>)'
        nav_replacement = f'''\\1
{nav_prev}
  <a href="/blog" class="bg-surface border border-outline-variant/20 border-l-[3px] border-l-transparent hover:border-l-secondary-accent rounded-sm px-4 py-3 font-mono text-sm group no-underline flex items-center">
    <span class="text-on-surface-variant group-hover:text-secondary-accent transition-colors">all posts</span>
  </a>
{nav_next}
\\2'''

        new_content = re.sub(nav_pattern, nav_replacement, content, flags=re.DOTALL)
        if new_content != content:
            post_path.write_text(new_content, encoding="utf-8")
            print(f"  Updated nav in {post['slug']}/index.html")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# RSS feed generator
# ---------------------------------------------------------------------------
def generate_rss(posts=None):
    """Generate RSS 2.0 feed at feed/index.xml."""
    if posts is None:
        posts = load_all_posts()

    if not posts:
        print("WARNING: No posts found, skipping RSS generation")
        return

    feed_dir = SITE_ROOT / "feed"
    feed_dir.mkdir(exist_ok=True)

    items = []
    for post in posts:
        # Strip HTML from excerpt for RSS description
        description = re.sub(r'<[^>]+>', '', html.unescape(post.get("excerpt", "")))
        title = html.unescape(re.sub(r'&\w+;', lambda m: html.unescape(m.group()), post["title"]))
        link = f"{SITE_URL}/blog/{post['slug']}/"
        # RFC 822 date format for RSS
        try:
            dt = datetime.strptime(post["date"], "%Y-%m-%d")
            pub_date = dt.strftime("%a, %d %b %Y 00:00:00 +0000")
        except ValueError:
            pub_date = post["date"]

        # Full content for content:encoded (with relative URLs made absolute)
        content_html = post.get("content_html", "")
        if content_html:
            content_html = re.sub(r'(src|href)="/', rf'\1="{SITE_URL}/', content_html)
        content_encoded = f"\n      <content:encoded><![CDATA[{content_html}]]></content:encoded>" if content_html else ""

        # Image enclosure for feed readers
        og_image = post.get("og_image", "")
        enclosure = ""
        if og_image:
            enclosure = f'\n      <enclosure url="{html.escape(og_image)}" type="image/png" length="0"/>'

        items.append(f"""    <item>
      <title>{html.escape(title)}</title>
      <link>{link}</link>
      <guid isPermaLink="true">{link}</guid>
      <pubDate>{pub_date}</pubDate>
      <description>{html.escape(description)}</description>{content_encoded}{enclosure}
    </item>""")

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>terminal velocity_</title>
    <link>{SITE_URL}/blog/</link>
    <description>Hot takes on product, AI and fintech. Occasionally correct.</description>
    <language>en</language>
    <atom:link href="{SITE_URL}/feed/index.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
  </channel>
</rss>"""

    feed_path = feed_dir / "index.xml"
    feed_path.write_text(rss, encoding="utf-8")
    print(f"  Generated feed/index.xml ({len(posts)} posts)")


def truncate(text, max_len):
    """Truncate text with ellipsis."""
    # Strip HTML entities for length check
    plain = html.unescape(re.sub(r'&\w+;', ' ', text))
    if len(plain) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "..."


def estimate_read_time(html_content):
    """Estimate reading time from HTML content."""
    text = re.sub(r'<[^>]+>', '', html_content)
    words = len(text.split())
    minutes = max(1, round(words / 200))
    return f"{minutes} min read"



# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 publish.py <markdown-file> [--dry-run]")
        print("       python3 publish.py --rss")
        print("       python3 publish.py --rebuild-all")
        print()
        print("Example:")
        print("  python3 publish.py blog/drafts/my-new-post.md")
        print("  python3 publish.py --rss            # regenerate RSS feed only")
        print("  python3 publish.py --rebuild-all     # refresh all posts with current components")
        print()
        print("Create blog/drafts/ and put your .md files there.")
        sys.exit(1)

    # Standalone RSS generation
    if sys.argv[1] == "--rss":
        posts = load_all_posts()
        generate_rss(posts)
        return

    # Rebuild all existing posts with current components
    if sys.argv[1] == "--rebuild-all":
        posts = load_all_posts()
        if not posts:
            print("No posts found.")
            return
        print(f"Rebuilding {len(posts)} post(s) with current components...")
        for i, post in enumerate(posts):
            # Determine prev/next for navigation
            prev_post = posts[i + 1] if i + 1 < len(posts) else None
            next_post = posts[i - 1] if i > 0 else None
            # Extract og:image path from the stored og_image URL
            og_image = post.get("og_image", "")
            if og_image.startswith(SITE_URL):
                og_image = og_image[len(SITE_URL):]
            # Build meta dict matching generate_post_html expectations
            meta = {
                "slug": post["slug"],
                "title": post["title"],
                "subtitle": post.get("subtitle", ""),
                "date": post["date"],
                "read_time": post.get("read_time", ""),
                "excerpt": post.get("excerpt", ""),
                "image": og_image or "/assets/og-card.png",
            }
            content_html = post.get("content_html", "")
            if not content_html:
                print(f"  SKIP {post['slug']} (no content extracted)")
                continue
            page_html = generate_post_html(meta, content_html, prev_post, next_post)
            out_path = BLOG_DIR / post["slug"] / "index.html"
            out_path.write_text(page_html, encoding="utf-8")
            print(f"  Rebuilt {post['slug']}/index.html")
        # Also regenerate landing, writing tab, and RSS
        generate_blog_landing(posts)
        update_writing_tab(posts)
        generate_rss(posts)
        print("Done.")
        return

    md_path = Path(sys.argv[1])
    dry_run = "--dry-run" in sys.argv

    if not md_path.exists():
        print(f"ERROR: File not found: {md_path}")
        sys.exit(1)

    print(f"{'[DRY RUN] ' if dry_run else ''}Publishing: {md_path.name}")
    print()

    # Parse
    raw = md_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)

    slug = meta["slug"]
    title = meta["title"]
    date = meta["date"]
    subtitle = meta.get("subtitle", "")
    excerpt = meta.get("excerpt", "")
    read_time = meta.get("read_time", "")

    print(f"  Title:    {title}")
    print(f"  Subtitle: {subtitle or '(none)'}")
    print(f"  Slug:     {slug}")
    print(f"  Date:     {date}")

    # Convert markdown to HTML
    content_html = md_to_html(body)

    if not read_time:
        read_time = estimate_read_time(content_html)
    meta["read_time"] = read_time

    print(f"  Read:     {read_time}")
    print()

    # Create output directory
    output_dir = BLOG_DIR / slug
    output_file = output_dir / "index.html"

    if output_file.exists() and "--force" not in sys.argv:
        print(f"WARNING: {output_file} already exists. Use --force to overwrite.")
        response = input("Overwrite? [y/N] ").strip().lower()
        if response != "y":
            print("Aborted.")
            sys.exit(0)

    if dry_run:
        print("[DRY RUN] Would create:")
        print(f"  {output_file}")
        print(f"  Update blog/index.html")
        print(f"  Update index.html Writing tab")
        print(f"  Update prev/next nav on adjacent posts")
        return

    # Create post directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # We need to know prev/next posts, so load all first, add the new one
    posts = load_all_posts()

    # Check if this slug already exists in posts list
    existing_slugs = {p["slug"] for p in posts}
    new_post_meta = {
        "slug": slug,
        "title": smart_quotes(title),
        "subtitle": smart_quotes(subtitle),
        "date": date,
        "read_time": read_time,
        "excerpt": excerpt or extract_excerpt(body),
    }

    if slug not in existing_slugs:
        posts.append(new_post_meta)
        posts.sort(key=lambda p: p["date"], reverse=True)

    # Find this post's neighbors
    idx = next(i for i, p in enumerate(posts) if p["slug"] == slug)
    prev_post = posts[idx + 1] if idx + 1 < len(posts) else None
    next_post = posts[idx - 1] if idx > 0 else None

    # Generate post HTML
    post_html = generate_post_html(meta, content_html, prev_post, next_post)
    output_file.write_text(post_html, encoding="utf-8")
    print(f"  Created {output_file}")

    # Reload posts (now includes the new one)
    posts_updated = load_all_posts()

    # Update blog landing page
    generate_blog_landing(posts_updated)
    print(f"  Updated blog/index.html")

    # Update Writing tab on main page
    update_writing_tab(posts_updated)

    # Update prev/next nav on all posts
    update_adjacent_nav(posts_updated)

    # Regenerate RSS feed
    generate_rss(posts_updated)

    print()
    print("Done! Preview your post at:")
    print(f"  file://{output_file}")


def extract_excerpt(md_body):
    """Extract first paragraph from markdown body as excerpt."""
    for line in md_body.split("\n"):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith(">") and not stripped.startswith("-"):
            # Strip markdown formatting
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', stripped)
            text = re.sub(r'\*(.+?)\*', r'\1', text)
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
            text = re.sub(r'`([^`]+)`', r'\1', text)
            return text[:200]
    return ""


if __name__ == "__main__":
    main()
