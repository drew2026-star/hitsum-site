"""Site checker: parses each page and enforces structure, SEO tags, link
integrity and the copy guardrails from the spec.

    python3 tools/sitecheck.py [root]
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

ORIGIN = "https://hitsum.app"

PAGES: dict[str, str | None] = {
    "index.html": f"{ORIGIN}/",
    "setup/index.html": f"{ORIGIN}/setup/",
    "support/index.html": f"{ORIGIN}/support/",
    "privacy/index.html": f"{ORIGIN}/privacy/",
    "404.html": None,
}

# Other launch monitors: the site never compares itself to them.
MONITORS = r"garmin|rapsodo|track\s?man|true\s?carry|foresight|sky\s?trak|mevo"

SOCIAL_TAGS = ["og:title", "og:description", "og:image", "og:url", "twitter:card"]


@dataclass
class Page:
    path: str = ""
    title: str = ""
    meta: dict[str, str] = field(default_factory=dict)
    canonical: str | None = None
    h1s: list[str] = field(default_factory=list)
    h2s: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    images: list[dict[str, str]] = field(default_factory=list)
    ids: set[str] = field(default_factory=set)
    text: str = ""
    cta_begin: int = 0
    cta_end: int = 0
    jsonld: list[dict] = field(default_factory=list)
    lang: str | None = None
    stylesheets: list[str] = field(default_factory=list)
    scripts: list[str] = field(default_factory=list)
    details_count: int = 0
    alts: list[str] = field(default_factory=list)
    placeholders: list[str] = field(default_factory=list)


class _Parser(HTMLParser):
    def __init__(self, page: Page):
        super().__init__(convert_charrefs=True)
        self.page = page
        self.stack: list[str] = []
        self.capture: str | None = None  # "title" | "h1" | "h2" | "jsonld"
        self.buf: list[str] = []
        self.text: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        p = self.page
        if "id" in a:
            p.ids.add(a["id"])
        if tag == "html":
            p.lang = a.get("lang")
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                p.meta[key] = a.get("content", "")
        elif tag == "link":
            rel = a.get("rel", "").split()
            if "canonical" in rel:
                p.canonical = a.get("href")
            if "stylesheet" in rel:
                p.stylesheets.append(a.get("href", ""))
        elif tag == "a" and "href" in a:
            p.links.append(a["href"])
        elif tag == "img" or (tag == "source" and "srcset" in a):
            p.images.append({"tag": tag, **a})
            if a.get("alt"):
                p.alts.append(a["alt"])
        elif tag == "body":
            # </head> is optional: leaving the head open would hide all body text.
            while "head" in self.stack:
                self.stack.pop()
        elif tag == "script":
            if "src" in a:
                p.scripts.append(a["src"])
            elif a.get("type") == "application/ld+json":
                self.capture, self.buf = "jsonld", []
        elif tag == "details":
            p.details_count += 1
        if tag in ("title", "h1", "h2"):
            self.capture, self.buf = tag, []
        if tag not in ("meta", "link", "img", "source", "br", "hr", "input"):
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if self.capture == tag or (self.capture == "jsonld" and tag == "script"):
            content = "".join(self.buf)
            if self.capture == "jsonld":
                self.page.jsonld.append(json.loads(content))
            else:
                content = " ".join(content.split())
                if self.capture == "title":
                    self.page.title = content
                elif self.capture == "h1":
                    self.page.h1s.append(content)
                else:
                    self.page.h2s.append(content)
            self.capture = None
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass

    def handle_data(self, data):
        if self.capture:
            self.buf.append(data)
        if not any(t in ("script", "style", "title", "head") for t in self.stack):
            self.text.append(data)

    def handle_comment(self, data):
        marker = data.strip()
        if marker == "CTA:BEGIN":
            self.page.cta_begin += 1
        elif marker == "CTA:END":
            self.page.cta_end += 1


def parse_page(html: str, path: str = "") -> Page:
    page = Page(path=path)
    parser = _Parser(page)
    parser.feed(html)
    parser.close()
    page.text = " ".join(" ".join(parser.text).split())
    page.placeholders = sorted(set(re.findall(r"APP_STORE_URL|APP_ID", html)))
    return page


def check_copy(text: str) -> list[str]:
    problems = []
    if re.search(r"\d\s?(%|per\s?cent)", text, re.I):
        problems.append("percentage")
    if re.search(r"\bR10\b", text) or re.search(MONITORS, text, re.I):
        problems.append("monitor comparison")
    if re.search(r"[$£€]\s?\d|\d\.\d{2}\s*/\s*(mo|month|yr|year)\b", text, re.I):
        problems.append("price")
    if re.search(r"\bside[\s\-\u2010\u2011]?on\b", text, re.I):
        problems.append("superseded placement wording")
    for m in re.finditer(r"android", text, re.I):
        if "not yet" not in text[m.end():m.end() + 80].lower():
            problems.append("android claim")
            break
    return problems


def _target_file(url_path: str) -> str:
    """Site-relative file a root-relative URL path is served from."""
    if url_path.endswith("/"):
        return url_path[1:] + "index.html"
    return url_path[1:]


def check_page(page: Page, root: Path) -> list[str]:
    problems = []
    if page.lang != "en":
        problems.append('<html lang="en"> missing')
    if "viewport" not in page.meta:
        problems.append("viewport meta missing")
    if not page.title:
        problems.append("title missing")
    desc = page.meta.get("description", "")
    if not 50 <= len(desc) <= 160:
        problems.append(f"meta description is {len(desc)} chars, want 50-160")
    want = PAGES.get(page.path)
    if page.path == "404.html":
        if page.canonical is not None:
            problems.append("404 must not have a canonical")
        if "noindex" not in page.meta.get("robots", ""):
            problems.append("404 needs robots noindex")
    else:
        if page.canonical != want:
            problems.append(f"canonical is {page.canonical!r}, want {want!r}")
        for tag in SOCIAL_TAGS:
            if not page.meta.get(tag):
                problems.append(f"{tag} missing")
    if len(page.h1s) != 1:
        problems.append(f"want exactly one h1, found {len(page.h1s)}")
    if "/style.css" not in page.stylesheets:
        problems.append("/style.css not linked")
    for src in page.scripts:
        problems.append(f"script not allowed: {src}")
    if page.cta_begin != page.cta_end:
        problems.append(f"CTA markers unbalanced: {page.cta_begin} BEGIN, {page.cta_end} END")

    for img in page.images:
        urls = []
        if img["tag"] == "img":
            if not img.get("alt"):
                problems.append(f"img {img.get('src')} has no alt")
            for attr in ("width", "height"):
                if not img.get(attr):
                    problems.append(f"img {img.get('src')} has no {attr}")
            urls.append(img.get("src", ""))
        if img.get("srcset"):
            urls += [part.strip().split()[0] for part in img["srcset"].split(",") if part.strip()]
        for url in urls:
            if url.startswith("/") and not (root / url[1:]).is_file():
                problems.append(f"image missing: {url}")

    for name in page.placeholders:
        problems.append(f"release placeholder {name} left in the page")

    own_ids = page.ids
    for href in page.links:
        if href.startswith(ORIGIN + "/"):
            href = href[len(ORIGIN):]
        elif not href.startswith(("/", "#", "http:", "https:", "mailto:", "tel:")):
            problems.append(f"use a root-relative link: {href}")
            continue
        if href.startswith("#"):
            if href[1:] not in own_ids:
                problems.append(f"missing anchor {href} on this page")
            continue
        if not href.startswith("/"):
            continue
        url_path, _, frag = href.partition("#")
        last = url_path.rsplit("/", 1)[-1]
        if not url_path.endswith("/") and "." not in last:
            problems.append(f"directory link without trailing slash: {href}")
            continue
        target = root / _target_file(url_path)
        if not target.is_file():
            problems.append(f"link target missing: {href}")
            continue
        if frag:
            if target.suffix == ".html":
                ids = parse_page(target.read_text(), _target_file(url_path)).ids
                if frag not in ids:
                    problems.append(f"missing anchor #{frag} in {href}")

    seen = " ".join([page.text, page.title, *page.meta.values(), *page.alts,
                     *(json.dumps(j, ensure_ascii=False) for j in page.jsonld)])
    for problem in check_copy(seen):
        if problem not in problems:
            problems.append(problem)
    return problems


def check_site(root: Path) -> list[str]:
    problems = []
    cname = root / "CNAME"
    if not cname.is_file() or cname.read_text().strip() != "hitsum.app":
        problems.append("CNAME: must contain hitsum.app")
    if not (root / ".nojekyll").is_file():
        problems.append(".nojekyll missing")
    robots = root / "robots.txt"
    if not robots.is_file() or f"Sitemap: {ORIGIN}/sitemap.xml" not in robots.read_text():
        problems.append("robots.txt must point to the sitemap")
    sitemap = root / "sitemap.xml"
    want = {u for u in PAGES.values() if u}
    if not sitemap.is_file():
        problems.append("sitemap.xml missing")
    else:
        locs = set(re.findall(r"<loc>\s*(.*?)\s*</loc>", sitemap.read_text()))
        if locs != want:
            problems.append(f"sitemap.xml locs {sorted(locs)} != {sorted(want)}")
    for rel in PAGES:
        f = root / rel
        if not f.is_file():
            problems.append(f"{rel}: missing")
            continue
        problems += [f"{rel}: {p}" for p in check_page(parse_page(f.read_text(), rel), root)]
    return problems


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent.parent
    problems = check_site(root)
    for p in problems:
        print(p)
    if problems:
        return 1
    print(f"OK ({len(PAGES)} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
