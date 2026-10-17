# hitsum.app

Marketing site for HitSum, the iPhone golf launch monitor and shot tracer by Kiki Gadgets Ltd.
Plain HTML and one stylesheet, served by GitHub Pages behind Cloudflare. No build step, no JavaScript.

- Design spec: `docs/superpowers/specs/2026-10-16-hitsum-marketing-site-design.md`
- Release-day checklist: `RELEASE.md`

## Pages

| URL | File |
|---|---|
| `/` | `index.html` |
| `/setup/` | `setup/index.html` |
| `/support/` | `support/index.html` |
| `/privacy/` | `privacy/index.html` |
| (not found) | `404.html` |

Every page repeats the same header and footer block. Change one, change all five.

## Preview

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000/.

## Test

```bash
python3 -m unittest discover -s tests
```

```bash
python3 tools/sitecheck.py
```

`sitecheck` enforces titles, descriptions, canonical and social tags, one H1 per page, image
alt/size attributes, internal links and anchors, and the copy rules: no accuracy percentages,
no comparisons with other launch monitors, no prices, no "side-on", and no Android claims.
Iframes must use YouTube's privacy-enhanced player (`youtube-nocookie.com`), carry a `title` and
load lazily; that setup video is the only third-party content on the site.

## Images

`assets/img` is generated from the app repo (`~/AndroidStudioProjects/golftrace`) and committed.
Re-run only when a screenshot, the icon or the wordmark changes:

```bash
python3 tools/build_images.py
```

## Copy source of truth

Setup wording follows the app: `ios/Sources/GolfTraceAppCore/Tutorial.swift` and `GolferCopy.swift`
in the golftrace repo. The privacy page is `docs/legal/privacy.md` there.

## Publish

Push to `main`. GitHub Pages serves the repo root at `hitsum.app` (see `CNAME`).
