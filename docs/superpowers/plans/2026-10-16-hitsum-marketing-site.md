# HitSum Marketing Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the four-page static HitSum site (Home, Setup, Support, Privacy, plus 404) in `~/hitsum-site`, ready to publish on GitHub Pages at `https://hitsum.app`.

**Architecture:** Hand-written HTML pages share one `style.css` and have no JavaScript. A stdlib-only Python checker (`tools/sitecheck.py`) is the test harness. It parses each page and enforces structure, SEO tags, link integrity and the copy guardrails, and per-page unittest files pin each page's required content. A Pillow script turns the app's raw screenshots and icon into web images once; its outputs are committed.

**Tech Stack:** HTML5, CSS (custom properties, `clamp()`, grid), Python 3 stdlib (`html.parser`, `unittest`, `http.server`), Pillow 11 (already installed), GitHub Pages, Cloudflare.

**Spec:** `docs/superpowers/specs/2026-10-16-hitsum-marketing-site-design.md`

## Global Constraints

- Canonical origin is `https://hitsum.app`. Internal links are root-relative and directory links end in `/` (e.g. `/setup/`, never `/setup` or `/setup/index.html`).
- **Copy guardrails** (enforced by the checker on every page):
  - No percentages. The privacy page is exempt only if the source policy contains one; it doesn't.
  - No "R10" and no "Garmin" or any other monitor comparison.
  - No prices: no `$` followed by a digit.
  - "Android" appears only when "not yet" follows within 80 characters.
  - No "side-on", which is the superseded placement wording.
- **Setup wording comes from the app, verbatim where quoted:**
  - Source files: `~/AndroidStudioProjects/golftrace/ios/Sources/GolfTraceAppCore/Tutorial.swift` and `GolferCopy.swift`.
  - Placement: directly behind the ball, 7.5 ft (2.3 m), two driver lengths.
  - Carry and apex are estimated (grey). Ball speed, launch and direction are measured (lime).
- Colors: `--bg #121315`, `--surface #1b1d1f`, `--text #ecedee`, `--text-muted #9aa0a6`, `--lime #c8f542`.
- Fonts: `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` for text, `ui-monospace, "SF Mono", Menlo, monospace` for numerals. No web fonts.
- Dark theme only. No JavaScript files. No third-party requests (no analytics, fonts, or CDNs).
- Support email: `support@kikigadgetsltd.com`. Publisher: Kiki Gadgets Ltd.
- Pre-release CTA text is exactly `Coming to the App Store · Nov 7`, wrapped in `<!-- CTA:BEGIN -->` … `<!-- CTA:END -->`.
- No prices for Premium. Describe monthly or yearly, with a 7-day free trial on yearly.

## Review Focus

1. **A 320px-wide phone.** Long headings, the CTA pill and the feature images must not cause horizontal scroll. Pinned in Task 8 Step 2 (browser `scrollWidth` check at 320/375/768/1280).
2. **Deep links from Support and the FAQ to `/setup/#…` anchors.** A renamed section id silently breaks them. Pinned by `sitecheck` anchor resolution (Task 1 test `test_missing_anchor_is_reported`).
3. **Links without a trailing slash** (`/setup`). GitHub Pages redirects them, but behind Cloudflare a redirect can drop the fragment. Pinned by Task 1 test `test_directory_link_without_slash_is_reported`.
4. **Muted grey text on the dark background** failing contrast for older golfers in sunlight. Pinned in Task 2 test `test_muted_text_contrast`.
5. **New copy reintroducing a forbidden claim** (a percentage, a price, "side-on", Android) during later edits, such as on release day. Pinned by Task 1 `check_copy` tests and run on every page by `check_site`.

---

## File Structure

```
hitsum-site/
  CNAME                      # "hitsum.app"
  .nojekyll                  # empty; lets /.well-known/ publish later
  robots.txt  sitemap.xml
  style.css                  # all styles; tokens on :root
  index.html  404.html
  setup/index.html  support/index.html  privacy/index.html
  assets/img/                # outputs of tools/build_images.py (committed)
  tools/sitecheck.py         # page parser + site rules + CLI
  tools/build_images.py      # one-shot image pipeline from the golftrace repo
  tests/test_sitecheck.py    # tests of the checker itself (fixtures inline)
  tests/test_site.py         # whole-site check + per-page content tests
  RELEASE.md  README.md
```

Run all tests with `python3 -m unittest discover -s tests -v` from the repo root.

---

### Task 1: Site checker (the test harness)

**Files:**
- Create: `tools/sitecheck.py`, `tests/test_sitecheck.py`, `tools/__init__.py` (empty), `.gitignore` (`__pycache__/`, `.DS_Store`)

**Interfaces:**
- Produces:
  - `Page` dataclass: `path: str`, `title: str`, `meta: dict[str, str]` (keyed by `name` or `property`), `canonical: str | None`, `h1s: list[str]`, `links: list[str]` (every `a[href]`), `images: list[dict[str, str]]` (attrs of each `img` and each `source[srcset]`), `ids: set[str]`, `text: str` (visible text, whitespace-collapsed, excluding `script`/`style`), `cta_begin: int`, `cta_end: int`, `jsonld: list[dict]`, `lang: str | None`, `stylesheets: list[str]`, `scripts: list[str]` (`script[src]`), `details_count: int`
  - `parse_page(html: str, path: str = "") -> Page`
  - `check_copy(text: str) -> list[str]`, which returns one message per guardrail violation
  - `check_page(page: Page, root: Path) -> list[str]`
  - `check_site(root: Path) -> list[str]`
  - `PAGES: dict[str, str | None]` = `{"index.html": "https://hitsum.app/", "setup/index.html": "https://hitsum.app/setup/", "support/index.html": "https://hitsum.app/support/", "privacy/index.html": "https://hitsum.app/privacy/", "404.html": None}`
  - CLI: `python3 tools/sitecheck.py [root]` prints each problem as `path: message` and exits 1 if any, else prints `OK (5 pages)` and exits 0.

**`check_page` rules:**
- `lang == "en"`.
- `meta["viewport"]` present.
- Non-empty `title`.
- `meta["description"]` is 50–160 characters.
- `canonical == PAGES[path]` (404 must have no canonical and must have `meta["robots"]` containing `noindex`).
- `og:title`, `og:description`, `og:image`, `og:url` and `twitter:card` are present on every page except 404.
- Exactly one H1.
- `/style.css` in stylesheets.
- `scripts == []`.
- `cta_begin == cta_end`.
- Every image has non-empty `alt` (a `source` needs no alt), plus `width` and `height`, and its `src`/each `srcset` URL exists under root.
- Every internal link (starts with `/`):
  - The target file exists (otherwise the message starts with `link target missing`): `/x/` maps to `x/index.html` and `/` maps to `index.html`; other paths map to themselves.
  - A path with no extension that doesn't end in `/` is reported as `directory link without trailing slash`.
  - A `#frag` must be in the target page's `ids`. A same-page `#frag` must be in its own `ids`.
- `mailto:` and `https:` links are not checked.
- `check_copy(page.text)` messages are appended.

**`check_copy` patterns** (case-insensitive unless noted):
- `\d\s?%` gives `percentage`.
- `\bR10\b` and `garmin` give `monitor comparison`.
- `\$\s?\d` gives `price`.
- `side-on` gives `superseded placement wording`.
- Any `android` with no `not yet` in the 80 characters that follow it gives `android claim`. This allows "Is there an Android version? Not yet."

**`check_site` rules:** every `PAGES` file exists and passes `check_page`. Also:
- `CNAME` stripped equals `hitsum.app`.
- `.nojekyll` exists.
- `robots.txt` contains `Sitemap: https://hitsum.app/sitemap.xml`.
- `sitemap.xml`'s `<loc>` set equals the non-None `PAGES` values.

- [ ] **Step 1: Write the failing tests** in `tests/test_sitecheck.py` (each builds a tiny HTML string or a temp dir via `tempfile.TemporaryDirectory`):

```python
GOOD = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>T</title>
<meta name="description" content="A description that is long enough to pass the fifty character floor.">
<link rel="canonical" href="https://hitsum.app/setup/"><link rel="stylesheet" href="/style.css">
<meta property="og:title" content="t"><meta property="og:description" content="d">
<meta property="og:image" content="https://hitsum.app/assets/img/og.png"><meta property="og:url" content="https://hitsum.app/setup/">
<meta name="twitter:card" content="summary_large_image"></head>
<body><h1 id="top">Setup</h1><a href="/setup/#top">x</a></body></html>"""

test_parse_page_extracts_fields           # title "T", canonical, h1s == ["Setup"], "top" in ids, links == ["/setup/#top"]
test_good_page_has_no_problems            # temp root with setup/index.html = GOOD and style.css → check_page(...) == []
test_two_h1s_are_reported                 # any message contains "h1"
test_missing_anchor_is_reported           # link "/setup/#nope" → message contains "#nope"
test_directory_link_without_slash_is_reported   # link "/setup" → "trailing slash"
test_missing_image_file_is_reported       # <img src="/assets/img/x.png" alt="a" width="1" height="1"> → "x.png"
test_image_without_alt_is_reported
test_script_tag_is_reported               # <script src="/a.js"> → "script"
test_unbalanced_cta_markers_are_reported  # one CTA:BEGIN, no END → "CTA"
test_copy_flags_percentage                # check_copy("off by 13%") == ["percentage"]
test_copy_flags_r10_garmin_price_sideon   # one message each for "R10", "Garmin", "$4.99", "side-on"
test_copy_allows_android_not_yet          # check_copy("Is there an Android version? Not yet.") == []
test_copy_flags_android_claim             # check_copy("Coming to Android soon.") == ["android claim"]
test_check_site_requires_cname_sitemap_robots   # empty temp root → messages mention CNAME, .nojekyll, robots, sitemap, index.html
```

- [ ] **Step 2: Run and confirm failure**

Run: `python3 -m unittest tests.test_sitecheck -v`
Expected: errors with `ModuleNotFoundError: No module named 'tools.sitecheck'`.

- [ ] **Step 3: Implement `tools/sitecheck.py`** to the interfaces and rules above, using `html.parser.HTMLParser`. The CTA markers are comments, counted in `handle_comment` (`"CTA:BEGIN"` / `"CTA:END"` after strip). JSON-LD is the text of `script[type="application/ld+json"]`, parsed with `json.loads`. These don't count in `scripts`, which holds only `script[src]`.

- [ ] **Step 4: Run and confirm pass**

Run: `python3 -m unittest tests.test_sitecheck -v`
Expected: 14 tests OK.

- [ ] **Step 5: Commit**

```bash
git add .gitignore tools tests/test_sitecheck.py
git commit -m "test: site checker for structure, links, SEO tags and copy guardrails"
```

---

### Task 2: Images, styles, shared shell, 404, and site files

**Files:**
- Create: `tools/build_images.py`, `assets/img/*` (generated), `style.css`, `404.html`, `CNAME`, `.nojekyll`, `robots.txt`, `sitemap.xml`, `tests/test_site.py`

**Interfaces:**
- Consumes: `tools.sitecheck` (Task 1).
- Produces:
  - In `tests/test_site.py`: `page_problems(rel: str) -> list[str]` returns `check_page(parse_page(...), ROOT)` minus messages starting with `link target missing`. Pages link to pages built in later tasks, so per-page tests use this helper, and full link integrity is enforced by `test_check_site_clean` in Task 7.
  - **Image files** (exact names; later tasks reference them):
    - `assets/img/shot-{run,analysis,hole,trace,arcs}-{480,960}.webp` and `shot-{…}-960.png`
    - `assets/img/wordmark.svg`
    - `assets/img/icon-180.png` (apple-touch-icon), `assets/img/favicon-32.png`, `assets/img/favicon.svg` only if the icon is vector (it isn't, so skip)
    - `assets/img/og.png` (1200×630)
  - **CSS classes** later pages use:
    - `.wrap` (max-width 1100px, 16px gutters)
    - `.site-header` / `.site-footer`, `.nav`
    - `.hero`, `.cta-pill`, `.lime`
    - `.feature` (two columns at ≥768px; add `.feature--flip` to put the image on the right), `.phone` (screenshot: rounded corners `border-radius: 12%/5.5%`, shadow, max-width 320px)
    - `.steps` (an ordered list styled as numbered cards), `.split` (two columns at ≥768px)
    - `.faq details` (on `--surface`, with a visible focus ring on `summary`)
    - `.prose` (long-form text for Setup, Support, Privacy)
    - `.stat` (monospace numerals)
    - `.est` (grey "EST" tag like the app)
  - **Shared shell markup.** Copy this block verbatim into every page. It's the only shared markup.

```html
<header class="site-header"><div class="wrap nav">
  <a href="/" class="brand"><img src="/assets/img/wordmark.svg" alt="HitSum" width="117" height="40"></a>
  <nav aria-label="Main"><a href="/setup/">Setup</a><a href="/support/">Support</a></nav>
</div></header>
…
<footer class="site-footer"><div class="wrap">
  <p>© 2026 Kiki Gadgets Ltd · <a href="/privacy/">Privacy</a> · <a href="/support/">Support</a></p>
  <p class="muted">Course data © OpenStreetMap contributors, available under the Open Database License (ODbL).</p>
</div></footer>
```

  - **Head template** for every page: `charset`, viewport, title, description, canonical, OG and Twitter tags (`og:image` = `https://hitsum.app/assets/img/og.png`, `twitter:card` = `summary_large_image`), `<meta name="theme-color" content="#121315">`, `<link rel="icon" href="/assets/img/favicon-32.png">`, `<link rel="apple-touch-icon" href="/assets/img/icon-180.png">`, `<link rel="stylesheet" href="/style.css">`.

- [ ] **Step 1: Write the failing tests** in `tests/test_site.py`:

```python
ROOT = Path(__file__).resolve().parent.parent

class SiteFiles(unittest.TestCase):
    def test_image_outputs_exist(self):
        for stem in ["run", "analysis", "hole", "trace", "arcs"]:
            for f in [f"shot-{stem}-480.webp", f"shot-{stem}-960.webp", f"shot-{stem}-960.png"]:
                self.assertTrue((ROOT / "assets/img" / f).is_file(), f)
        self.assertEqual(Image.open(ROOT / "assets/img/og.png").size, (1200, 630))
        self.assertEqual(Image.open(ROOT / "assets/img/icon-180.png").size, (180, 180))
    def test_wordmark_has_no_c2pa_metadata(self):     # "c2pa" not in wordmark.svg text; file < 6000 bytes
    def test_css_tokens(self):                          # style.css contains each Global Constraints color token exactly
    def test_muted_text_contrast(self):                 # WCAG contrast(--text-muted, --bg) >= 4.5 and (--text, --bg) >= 7; compute from the hex in style.css
    def test_404_page_passes(self):                     # page_problems("404.html") == []
```

- [ ] **Step 2: Run and confirm failure**

Run: `python3 -m unittest tests.test_site -v`
Expected: `SiteFiles` tests fail (missing files).

- [ ] **Step 3: Implement `tools/build_images.py`** (`main() -> None`, run as `python3 tools/build_images.py`).
  - `SRC = Path.home() / "AndroidStudioProjects/golftrace/design"`.
  - Screenshots, mapping output stem to raw source:
    - `run` → `appstore/raw/iphone/1-run.png`
    - `analysis` → `appstore/raw/device/analysis.png`
    - `hole` → `appstore/raw/device/hole.png`
    - `trace` → `appstore/raw/device/trace.png`
    - `arcs` → `appstore/raw/device/arcs.png`
  - For the four `device/` captures, first replace the real status bar. Import `clean_status_bar` from `golftrace/tools/appstore/frame.py` by adding that directory to `sys.path`. Its behaviour: paint the top 160px with `#121315` and paste the 400px left and right clusters from `1-run.png`.
  - Resize each screenshot to 480 and 960px wide (LANCZOS). Save WebP at quality 82, plus the 960 PNG (optimize=True).
  - Wordmark: copy `photos/export/wordmark/svg/HitSum-Wordmark-Small.svg` with the `<metadata>…</metadata>` element removed (regex, DOTALL).
  - Icons: `icons/AppIcon-comet-1024.png` resized to 180 and 32.
  - `og.png`: `appstore/upload/header-16x9.png` (5244×2950) resized to cover 1200×630 and center-cropped.

  Run it, then open `assets/img/shot-hole-960.webp` and `shot-trace-960.webp` to confirm the status bar reads 9:41 with nothing personal in view.

- [ ] **Step 4: Write `style.css`, `404.html` and the site files.**
  - `style.css`: tokens on `:root`, `body { background: var(--bg); color: var(--text) }`, and the classes listed above. Mobile-first, two-column rules under `@media (min-width: 768px)`. Headings use `clamp()`: H1 `clamp(2.2rem, 7vw, 4rem)`, `overflow-wrap: anywhere`.
  - `404.html`: shell + `<h1>Page not found</h1>`, one line, links to `/` and `/setup/`, plus `<meta name="robots" content="noindex">`.
  - `CNAME`: `hitsum.app`.
  - `.nojekyll`: empty.
  - `robots.txt`: `User-agent: *`, `Allow: /`, `Sitemap: https://hitsum.app/sitemap.xml`.
  - `sitemap.xml`: the four canonical URLs, with `<lastmod>2026-10-16</lastmod>`.

- [ ] **Step 5: Run and confirm pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all tests OK.

- [ ] **Step 6: Commit**

```bash
git add tools/build_images.py assets style.css 404.html CNAME .nojekyll robots.txt sitemap.xml tests/test_site.py
git commit -m "feat: images, shared styles, 404 and site files"
```

---

### Task 3: Home page

**Files:**
- Create: `index.html`
- Modify: `tests/test_site.py` (add `class Home`)

**Interfaces:**
- Consumes: shell, head template, CSS classes and image names from Task 2.
- Produces: section ids `features`, `honest`, `setup-steps`, `free-premium`, `faq`, and FAQ `details` ids `faq-iphones`, `faq-slowmo`, `faq-indoors`, `faq-accuracy`, `faq-spin`, `faq-altitude`, `faq-android`, `faq-free`. Support (Task 5) links to `/#free-premium`.

- [ ] **Step 1: Write the failing tests** (`class Home`, using `parse_page(ROOT/"index.html")`):

```python
test_home_passes_page_check            # page_problems("index.html") == []
test_hero                              # h1s == ["Your iPhone is the launch monitor."]; "Nothing to buy, pair or charge." in text
test_two_cta_regions_with_prelaunch_text   # cta_begin == cta_end == 2; text.count("Coming to the App Store · Nov 7") == 2
test_sections_present                  # {"features","honest","setup-steps","free-premium","faq"} <= ids
test_faq_items                         # details_count == 8 and all eight faq-* ids in ids
test_setup_steps_match_app             # "directly behind the ball" in text; "7.5 ft (2.3 m)" in text; "two driver lengths" in text
test_estimated_values_named            # "Carry and apex" in text (honest-numbers strip)
test_free_tier                         # "15 measured shots a day" in text and "7-day free trial" in text
test_jsonld_software_application       # one jsonld with @type SoftwareApplication, operatingSystem "iOS",
                                       # applicationCategory "SportsApplication", offers.price "0"; "aggregateRating" not in it
test_links_to_setup                    # "/setup/" in links
test_hero_image_eager_rest_lazy        # first img has no loading="lazy"; every later img has loading="lazy"
```

- [ ] **Step 2: Run and confirm failure**

Run: `python3 -m unittest tests.test_site.Home -v`
Expected: errors, `index.html` not found.

- [ ] **Step 3: Write `index.html`** with the spec §5.1 sections in order, using the shell, the head template and these fixed choices:
  - **Title:** `HitSum: your iPhone is the golf launch monitor`.
  - **Description:** `Ball speed, launch and carry from every swing, measured from your iPhone's camera. Shot tracer and 3D range included. Free to start.`
  - **Hero:** subhead from the spec; CTA region 1; `.phone` image `shot-run`. Alt text: `HitSum launch monitor showing a 7 iron carry of 155 yards, ball speed 113 mph and launch 18.3 degrees`.
  - **Features**, each a `<picture>` with WebP `srcset` at 480w/960w, `sizes="(min-width: 768px) 320px, 80vw"` and a PNG fallback `img`:
    - Launch monitor → `shot-run`. Reuse is fine. If it looks repetitive next to the hero, use `shot-arcs` and say "every session, every shot".
    - Shot tracer → `shot-trace`.
    - See it land and know your bag → `shot-hole`, then a second `.phone` with `shot-analysis`.
  - **Honest numbers:** the spec §5.1 item 3 wording, with a `.stat` sample row showing lime `113 mph` / `18.3°` and grey `155 yd` with `.est`.
  - **Setup steps:** the spec §5.1 item 4 three steps, then `<a href="/setup/">Full setup guide</a>`.
  - **Free vs Premium:** the spec §5.1 item 5 lists, with no prices.
  - **FAQ:** the eight items with the answers in spec §5.1 item 6. The accuracy answer must be: `Ball speed, launch and direction are measured from high-speed video of the ball's flight. Carry and apex assume a typical spin for your club, so they're marked as estimates.` The altitude answer: `HitSum uses your phone's barometer to adjust for thin air.` The iPhones answer: `The launch monitor works best on iPhone 12 or later. iPads and older iPhones running iOS 17.2 or later can watch a friend's Join session.`
  - **Closing:** CTA region 2.
  - **JSON-LD:** `{"@context":"https://schema.org","@type":"SoftwareApplication","name":"HitSum","operatingSystem":"iOS","applicationCategory":"SportsApplication","offers":{"@type":"Offer","price":"0","priceCurrency":"USD"},"publisher":{"@type":"Organization","name":"Kiki Gadgets Ltd"}}`.

- [ ] **Step 4: Run and confirm pass**

Run: `python3 -m unittest tests.test_site.Home -v`
Expected: 11 tests OK.

- [ ] **Step 5: Look at it.** Run `python3 -m http.server 8000` in the background from the repo root and open `http://localhost:8000/` in the browser pane at 375px and 1280px. Check the hero CTA and image sit above the fold at 1280px and nothing scrolls horizontally at 375px.

- [ ] **Step 6: Commit**

```bash
git add index.html tests/test_site.py
git commit -m "feat: home page"
```

---

### Task 4: Setup guide

**Files:**
- Create: `setup/index.html`
- Modify: `tests/test_site.py` (add `class Setup`)

**Interfaces:**
- Produces: anchors `launch-monitor`, `shot-tracer`, `join`, `troubleshooting`, and tutorial slot ids `photo-securedPhone`, `photo-tapTheBall`, `photo-measuredAndEstimated`. Support (Task 5) deep-links to the first four.

- [ ] **Step 1: Write the failing tests** (`class Setup`):

```python
test_setup_passes_page_check   # page_problems("setup/index.html") == []
test_setup_anchors          # the four section ids and three photo-* ids are in ids
test_tutorial_titles_verbatim   # each in text: "Set up directly behind the ball", "Select your hitting area", "Lime is measured. Grey is estimated."
test_distance_copy          # "7.5 ft (2.3 m)" in text; "two driver lengths" in text;
                            # "A foot off at 7.5 ft puts every number off by" in text (the "13%" that follows is a percentage —
                            # write it as "off by about an eighth" instead; assert "eighth" in text)
test_troubleshooting_items  # each in text: "Too dark", "Not the ball", "sideways", "Missed"
test_title_and_h1           # h1s == ["Set up HitSum"]
```

- [ ] **Step 2: Run and confirm failure**

Run: `python3 -m unittest tests.test_site.Setup -v`
Expected: errors, `setup/index.html` not found.

- [ ] **Step 3: Write `setup/index.html`** (`.prose`). Title `Set up HitSum | HitSum`. Description of 50–160 characters about phone placement and getting good readings.
  - **Contents nav:** an unordered list of in-page links to the four sections.
  - **`#launch-monitor`:** the three tutorial cards as `h3` titles, verbatim from `Tutorial.swift`, with their bodies. Then a "Get the distance right" paragraph from `GolferCopy.distanceWhy` / `distanceHow`, with the 13% rephrased as "about an eighth". Then: shade the phone, and bright light (too dark means missed shots). Indoors: 8–10 ft from a net or screen.
    - Each card's figure is a `<figure id="photo-…">` holding a `.phone` screenshot for now: `shot-run` for measuredAndEstimated; the other two use a `figcaption` placeholder sentence and no image until the photos exist.
    - Above each figure, add an HTML comment naming the `TutorialArt` slot.
  - **`#shot-tracer`:** hold still and don't follow the ball; record, then mark the ball under the crosshair; check, then trace; share the clip. Figure: `shot-trace`.
  - **`#join`:** hosting is Premium. Watching is free on iPads and older iPhones running iOS 17.2 or later.
  - **`#troubleshooting`:** a definition list built from `GolferCopy` messages:
    - Too dark
    - Not the ball / no ball where you marked
    - The picture is sideways (turn rotation lock off)
    - Phone too hot or dropping frames (shade it)
    - "Missed that one", which links back to `#launch-monitor`
    - Numbers look off: check the measured distance

- [ ] **Step 4: Run and confirm pass**

Run: `python3 -m unittest tests.test_site.Setup -v`
Expected: 6 tests OK.

- [ ] **Step 5: Commit**

```bash
git add setup tests/test_site.py
git commit -m "feat: setup guide page"
```

---

### Task 5: Support page

**Files:**
- Create: `support/index.html`
- Modify: `tests/test_site.py` (add `class Support`)

**Interfaces:**
- Consumes: `/setup/#launch-monitor`, `/setup/#troubleshooting` (Task 4); `/#free-premium` (Task 3).

- [ ] **Step 1: Write the failing tests** (`class Support`):

```python
test_support_passes_page_check   # page_problems("support/index.html") == []
test_contact_mailto            # "mailto:support@kikigadgetsltd.com" in links; "support@kikigadgetsltd.com" in text
test_deep_links                # "/setup/#launch-monitor" in links and "/setup/#troubleshooting" in links and "/#free-premium" in links
test_subscription_help         # "Restore Purchases" in text; "24 hours" in text; any link starts with "https://support.apple.com/"
test_account_deletion          # "Delete account" in text or "delete your account" in text
test_h1                        # h1s == ["HitSum support"]
```

- [ ] **Step 2: Run and confirm failure**

Run: `python3 -m unittest tests.test_site.Support -v`
Expected: errors, `support/index.html` not found.

- [ ] **Step 3: Write `support/index.html`** (`.prose`). Title `Support | HitSum`. Sections:
  - **Contact:** the mailto link. Mention "Copy support ID" in Settings to include in the email; this string is from `GolferCopy.copySupportID`.
  - **Quick fixes:** three tips (behind the ball at 7.5 ft and measured; bright light and a shaded phone; tap the ball inside the circle), then links to the two setup anchors.
  - **Subscriptions:**
    - Manage or cancel in Apple ID settings, linking to `https://support.apple.com/en-us/118428`.
    - Renewal happens unless cancelled at least 24 hours before the period ends.
    - Restore Purchases in the app. Before writing the exact menu path, confirm the button label in the golftrace iOS sources with `grep -rn "Restore" ~/AndroidStudioProjects/golftrace/ios --include=*.swift`.
    - Link to `/#free-premium`.
  - **Account:** Sign in with Apple is optional; how to delete your account. Confirm the label and location with `grep -rn -i "delete account" ~/AndroidStudioProjects/golftrace/ios --include=*.swift` and write what the app says.
  - **Requirements:** iPhone 12 or later for the launch monitor; iOS 17.2+ to watch a Join session.

- [ ] **Step 4: Run and confirm pass**

Run: `python3 -m unittest tests.test_site.Support -v`
Expected: 6 tests OK.

- [ ] **Step 5: Commit**

```bash
git add support tests/test_site.py
git commit -m "feat: support page"
```

---

### Task 6: Privacy page

**Files:**
- Create: `privacy/index.html`
- Modify: `tests/test_site.py` (add `class Privacy`)

**Interfaces:**
- Consumes: `~/AndroidStudioProjects/golftrace/docs/legal/privacy.md` (80 lines, effective September 25, 2026).

- [ ] **Step 1: Write the failing tests** (`class Privacy`):

```python
SRC_MD = Path.home() / "AndroidStudioProjects/golftrace/docs/legal/privacy.md"

test_privacy_passes_page_check   # page_problems("privacy/index.html") == []
test_headings_match_source   # the md's "## " heading texts, in order, equal the page's h2 texts in order
                             # (add `h2s: list[str]` to Page in sitecheck.py with a test in test_sitecheck.py)
test_effective_date          # "September 25, 2026" in text
test_h1                      # h1s == ["HitSum Privacy Policy"]
test_publisher               # "Kiki Gadgets Ltd" in text
```

`test_headings_match_source` is skipped with `unittest.skipUnless(SRC_MD.exists(), ...)` so the suite still runs on machines without the app repo.

- [ ] **Step 2: Run and confirm failure**

Run: `python3 -m unittest tests.test_site.Privacy tests.test_sitecheck -v`
Expected: `privacy/index.html` not found, and the new `h2s` test fails.

- [ ] **Step 3: Add `h2s` to `Page`, then write `privacy/index.html`.** Hand-convert the Markdown into `.prose` HTML. Keep the wording exact: bold becomes `<strong>`, bullets become `<ul>`, and `→` stays as is. Title `Privacy Policy | HitSum`. Add a closing line linking to `/support/`.

- [ ] **Step 4: Run and confirm pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all tests OK.

- [ ] **Step 5: Commit**

```bash
git add privacy tools/sitecheck.py tests
git commit -m "feat: privacy page"
```

---

### Task 7: Whole-site check, release checklist, README

**Files:**
- Create: `RELEASE.md`, `README.md`
- Modify: `tests/test_site.py` (add `class WholeSite`)

- [ ] **Step 1: Add `class WholeSite` with `test_check_site_clean`**, asserting `check_site(ROOT) == []`, and run it.

Run: `python3 -m unittest tests.test_site.WholeSite -v`
Expected: OK. If it fails, fix the reported pages; don't weaken the check.

- [ ] **Step 2: Run the CLI**

Run: `python3 tools/sitecheck.py`
Expected: `OK (5 pages)`, exit 0.

- [ ] **Step 3: Write `RELEASE.md`.** A numbered checklist covering:
  1. Replace each `CTA:BEGIN…END` region (2 in `index.html`) with Apple's badge. Download it from Apple's Marketing Resources site and save it to `assets/badges/app-store-badge.svg`, with `alt="Download on the App Store"`, `width="120" height="40"`, linked to the App Store URL.
  2. Add `<meta name="apple-itunes-app" content="app-id=APP_ID">` to all 5 pages' `<head>`.
  3. Add `"downloadUrl"` / `"installUrl"` with the App Store URL to the home JSON-LD.
  4. Run `python3 -m unittest discover -s tests` and `python3 tools/sitecheck.py`. The CTA text tests in `Home` will fail by design: update them to assert the badge link.
  5. In App Store Connect, set the Support URL to `https://hitsum.app/support/` and the Privacy URL to `https://hitsum.app/privacy/`.
  6. Keep `kikigadgetsltd.com/privacy-hitsum.html` in sync with `privacy/index.html`, or replace it with a link.
  7. Set `AppLink.url` in the app repo.

- [ ] **Step 4: Write `README.md`:**
  - What the site is and where the spec lives.
  - How to preview: `python3 -m http.server 8000`.
  - How to test: the unittest command and the CLI.
  - How to regenerate images: `python3 tools/build_images.py`, which needs the golftrace repo at `~/AndroidStudioProjects/golftrace`.
  - That publishing is a push to `main`.

- [ ] **Step 5: Commit**

```bash
git add RELEASE.md README.md tests/test_site.py
git commit -m "docs: release-day checklist and README; whole-site check enforced"
```

---

### Task 8: Browser verification

No files change unless a check fails. A fix goes in the page or `style.css` with a commit of its own.

- [ ] **Step 1: Serve locally.** Run `python3 -m http.server 8000` in the background and open `http://localhost:8000/` in the browser pane.

- [ ] **Step 2: Overflow check at four widths.** For each of `/`, `/setup/`, `/support/`, `/privacy/`, `/404.html`:
  - Resize the pane to 320, 375, 768 and 1280 wide.
  - Run `document.documentElement.scrollWidth <= window.innerWidth`.
  - Expected: `true` for all 20 combinations.

- [ ] **Step 3: Visual pass.** Take a screenshot of `/` at 375 and 1280, and of `/setup/` at 375. Check:
  - Headings wrap cleanly.
  - The CTA pill is on one line at 375.
  - FAQ items open and close with click and keyboard (Tab to a summary, then Enter).
  - Anchor links from Support land on the right Setup section.

- [ ] **Step 4: Lighthouse (mobile)** on `/` and `/setup/`.

Run: `npx --yes lighthouse@12.2.1 http://localhost:8000/ --only-categories=performance,accessibility,seo --form-factor=mobile --quiet --chrome-flags="--headless" --output=json --output-path=/tmp/lh-home.json` (repeat with `/setup/` → `/tmp/lh-setup.json`), then print the three category scores from each JSON.
Expected: each score ≥ 0.90. If Chrome isn't installed, note it, skip this step, and report that Lighthouse wasn't run.

- [ ] **Step 5: Report** the results of Steps 2–4 to the owner, plus any commits made to fix failures.

---

### Task 9: Publish (owner-run, with exact values)

The executor prepares this list for the owner and **does not push or change DNS itself** without the owner's explicit go-ahead in chat. These steps act on the owner's GitHub and Cloudflare accounts.

1. **GitHub:** create the repo `hitsum-site`. Run `git remote add origin git@github.com:<owner>/hitsum-site.git` and `git push -u origin main`.
2. **Pages:** Settings → Pages → Source: Deploy from branch → `main` / `(root)`. Custom domain: `hitsum.app`. After the certificate is issued, tick Enforce HTTPS.
3. **Cloudflare DNS for `hitsum.app`.** Set to DNS only (grey cloud) until HTTPS is enforced on GitHub. After that, switching to Proxied is optional; if you do, set SSL/TLS mode to **Full**.
   - `A @` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `AAAA @` → `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`
   - `CNAME www` → `<owner>.github.io`
4. **Cloudflare, `hitsumgolf.com`:**
   - Records: `A @` → `192.0.2.1` (Proxied) and `CNAME www` → `hitsumgolf.com` (Proxied).
   - Rules → Redirect Rules → Single redirect with these settings:
     - When: hostname is in `hitsumgolf.com`, `www.hitsumgolf.com`
     - Then: dynamic, expression `concat("https://hitsum.app", http.request.uri.path)`
     - Status `301`, preserve query string
5. **Live checks** (the owner runs them, or the executor runs them once DNS has propagated):

```bash
curl -sI https://hitsum.app/ | head -1
```
Expected: `HTTP/2 200`

```bash
curl -sI http://hitsum.app/ | grep -i -E "^(HTTP|location)"
```
Expected: a 301 to `https://hitsum.app/`

```bash
curl -sI https://hitsumgolf.com/support/ | grep -i -E "^(HTTP|location)"
```
Expected: `301` and `location: https://hitsum.app/support/`

```bash
curl -sI https://www.hitsum.app/ | grep -i -E "^(HTTP|location)"
```
Expected: a 301 to `https://hitsum.app/`
