# terminalvelocity.me

Personal site. Plain static HTML and CSS – no JavaScript, no build step, no dependencies, no third-party requests. Fonts are self-hosted (JetBrains Mono + Inter, latin woff2, SIL OFL).

## Development

There is nothing to build. Edit the HTML, open it in a browser.

```bash
python3 -m http.server 8000   # local preview on :8000
```

## Deploy

Cloudflare Pages serves the repo as-is from `main`.

## Structure

- `index.html` – the whole homepage, CSS inlined
- `privacy/`, `imprint/`, `cv/`, `thanks/`, `404.html` – sub-pages, same design tokens
- `assets/` – portrait (AVIF/WebP/PNG), og-card, favicon, `fonts/`
- `design.md` – design system
- `_redirects` – Cloudflare Pages redirects (retired blog routes)

## Blog

The blog lives at [terminalvelocity.blog](https://terminalvelocity.blog) – Hugo + Bear Cub, source at [matoautomato/terminalvelocity.blog](https://github.com/matoautomato/terminalvelocity.blog).
