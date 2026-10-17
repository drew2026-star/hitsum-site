# hitsum.app

Marketing site for HitSum, the iPhone golf launch monitor and shot tracer by Kiki Gadgets Ltd.
Plain HTML and one stylesheet, served by GitHub Pages behind Cloudflare. No build step. The only
JavaScript is `assets/js/motion.js`, which plays the video clips while they're on screen, leaves
them still for visitors who prefer reduced motion, and runs the setup clip's "Sound on" button.

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
The site makes no third-party requests. If an iframe is ever added it must use YouTube's
privacy-enhanced player (`youtube-nocookie.com`), carry a `title` and load lazily.

## Images

`assets/img` and `assets/video` are generated from the app repo (`~/AndroidStudioProjects/golftrace`) and committed.
Re-run only when a screenshot, the icon, the wordmark, an App Store preview, the setup video
(`~/Documents/hitsum1-short.mp4`) or the tracer recording (`~/Downloads/DA0025FB-…MP4`)
changes (needs `ffmpeg`). Cut points live at the top of the script:

```bash
python3 tools/build_images.py
```

## Copy source of truth

Setup wording follows the app: `ios/Sources/GolfTraceAppCore/Tutorial.swift` and `GolferCopy.swift`
in the golftrace repo. The privacy page is `docs/legal/privacy.md` there.

## Publish

Push to `main`. GitHub Pages serves the repo root at `hitsum.app` (see `CNAME`).
