#!/usr/bin/env python3
"""
build.py — Assemble static pages from components + templates.

Usage:
    python3 build.py              # rebuild all pages
    python3 build.py --page index # rebuild one page
"""

import sys
from pathlib import Path

SITE_ROOT = Path(__file__).parent.resolve()
COMPONENTS_DIR = SITE_ROOT / "components"
PAGES_DIR = SITE_ROOT / "pages"

# ---------------------------------------------------------------------------
# Nav CTA variants
# ---------------------------------------------------------------------------
NAV_CTA_BOOKING_DESKTOP = '<button onclick="openBookingModal()" class="bg-primary text-white px-5 py-2.5 text-base font-mono lowercase rounded-sm hover:brightness-110 active:scale-95 transition-all shadow-sm"><span class="lang-en">book a call</span><span class="lang-de hidden">termin buchen</span></button>'

NAV_CTA_BOOKING_MOBILE = '<button onclick="openBookingModal(); closeMobileMenu();" class="bg-primary text-white px-5 py-2.5 text-base font-mono lowercase rounded-sm hover:brightness-110 active:scale-95 transition-all shadow-sm w-full"><span class="lang-en">book a call</span><span class="lang-de hidden">termin buchen</span></button>'

NAV_CTA_BACK_DESKTOP = '<a href="/" class="bg-primary text-white px-5 py-2.5 text-base font-mono lowercase rounded-sm hover:brightness-110 active:scale-95 transition-all shadow-sm"><span class="lang-en">back to site</span><span class="lang-de hidden">zur&uuml;ck zur seite</span></a>'

NAV_CTA_BACK_MOBILE = '<a href="/" class="bg-primary text-white px-5 py-2.5 text-base font-mono lowercase rounded-sm hover:brightness-110 active:scale-95 transition-all shadow-sm w-full text-center" onclick="closeMobileMenu()"><span class="lang-en">back to site</span><span class="lang-de hidden">zur&uuml;ck zur seite</span></a>'

# ---------------------------------------------------------------------------
# Page registry: key = page name, value = config
# ---------------------------------------------------------------------------
PAGES = {
    "index": {
        "template": "index.html",
        "output": "index.html",
        "has_modal": True,
        "nav_cta": "booking",
    },
    "blog-landing": {
        "template": "blog-landing.html",
        "output": "blog/index.html",
        "has_modal": True,
        "nav_cta": "booking",
    },
    "privacy": {
        "template": "privacy.html",
        "output": "privacy/index.html",
        "has_modal": False,
        "nav_cta": "back",
    },
    "imprint": {
        "template": "imprint.html",
        "output": "imprint/index.html",
        "has_modal": False,
        "nav_cta": "back",
    },
    "thanks": {
        "template": "thanks.html",
        "output": "thanks/index.html",
        "has_modal": False,
        "nav_cta": "back",
    },
}


def load_component(name):
    """Read a component file and return its contents."""
    return (COMPONENTS_DIR / f"{name}.html").read_text(encoding="utf-8")


def build_page(page_name, config):
    """Assemble a page from its template + components and write the output."""
    template_path = PAGES_DIR / config["template"]
    template = template_path.read_text(encoding="utf-8")

    # Load components
    head = load_component("head")
    nav = load_component("nav")
    footer = load_component("footer")
    scripts = load_component("scripts")

    # Choose CTA variant
    if config["nav_cta"] == "booking":
        cta_desktop = NAV_CTA_BOOKING_DESKTOP
        cta_mobile = NAV_CTA_BOOKING_MOBILE
    else:
        cta_desktop = NAV_CTA_BACK_DESKTOP
        cta_mobile = NAV_CTA_BACK_MOBILE

    # Replace CTA markers in nav
    nav = nav.replace("<!-- NAV_CTA_DESKTOP -->", cta_desktop)
    nav = nav.replace("<!-- NAV_CTA_MOBILE -->", cta_mobile)

    # Replace component markers in template
    html = template.replace("<!-- COMPONENT:head -->", head)
    html = html.replace("<!-- COMPONENT:nav -->", nav)
    html = html.replace("<!-- COMPONENT:footer -->", footer)
    html = html.replace("<!-- COMPONENT:scripts -->", scripts)

    # Handle optional modal
    if config["has_modal"]:
        modal = load_component("modal")
        html = html.replace("<!-- COMPONENT:modal -->", modal)
    else:
        html = html.replace("<!-- COMPONENT:modal -->\n", "")
        html = html.replace("<!-- COMPONENT:modal -->", "")

    # Write output
    output_path = SITE_ROOT / config["output"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"  Built {config['output']}")


def main():
    pages_to_build = PAGES

    if "--page" in sys.argv:
        idx = sys.argv.index("--page")
        if idx + 1 < len(sys.argv):
            name = sys.argv[idx + 1]
            if name not in PAGES:
                print(f"ERROR: Unknown page '{name}'. Available: {', '.join(PAGES.keys())}")
                sys.exit(1)
            pages_to_build = {name: PAGES[name]}
        else:
            print("ERROR: --page requires a page name")
            sys.exit(1)

    print(f"Building {len(pages_to_build)} page(s)...")
    for name, config in pages_to_build.items():
        build_page(name, config)
    print("Done.")


if __name__ == "__main__":
    main()
