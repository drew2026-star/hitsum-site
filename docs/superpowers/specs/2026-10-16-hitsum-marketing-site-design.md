# HitSum marketing site — design

**Date:** 2026-10-16
**Status:** Draft for review
**Source material:** `~/AndroidStudioProjects/golftrace/docs/app-store/` (launch plan §6, description, promo text), `design/appstore/upload/` (screenshots), `design/icons/AppIcon-comet-1024.png`, `docs/legal/privacy.md`

## 1. Purpose

A small marketing site for HitSum, the iPhone/iPad golf launch monitor and shot tracer by Kiki Gadgets Ltd.

The site has four jobs:

1. **Convert visitors into App Store installs.** Before release it builds anticipation; from release day it sends visitors to the App Store.
2. **Reduce bad first sessions.** A setup guide makes correct phone placement easy to find, which heads off "numbers are wrong" 1-star reviews.
3. **Satisfy App Store requirements.** It provides a Support URL and a Privacy Policy URL on the app's own domain.
4. **Be ready for share links.** It's structured so `/.well-known/apple-app-site-association` can be added later without rework.

**Success means:**
- The site is live on `https://hitsum.app` before release on **Sat 2026-11-07**.
- Every page works at phone width.
- Lighthouse scores 90+ on Performance, Accessibility and SEO.
- The release-day CTA swap is a one-file-per-page edit covered by a checklist.

## 2. Context and constraints

- **App status:** v1.0 (build 18) is submitted and in App Review. The listing's Privacy URL currently points to `https://www.kikigadgetsltd.com/privacy-hitsum.html` and Support is an email address. **Do not change the listing URLs while in review.** Update them with the release.
- **Platform:** iPhone (launch monitor works best on iPhone 12+) and iPad / older iPhones on iOS 17.2+ (for watching a Join session). There's no Android version, and the site must not imply one.
- **Copy guardrails (from the launch plan):**
  - Never publish accuracy percentages or comparisons to Garmin R10 or other monitors. "Measured from high-speed video" is the approved claim.
  - Spin is estimated, not measured. Say so.
  - Don't show Premium prices yet (owner decision 2026-10-16).
- **Owner:** solo developer; the budget is effectively $0. The setup must be something the owner can maintain by hand-editing files.

## 3. Decisions

| Decision | Choice | Why |
|---|---|---|
| Primary domain | `hitsum.app` | Short, matches the app name, already planned for share links |
| Secondary domain | `hitsumgolf.com` (+ `www.` of both) → 301 to `https://hitsum.app`, path preserved | One canonical site for SEO |
| Stack | Hand-written static HTML + one CSS file, no build step | Same as kikigadgets-site; zero cost; supports `.well-known` files |
| Hosting | GitHub Pages from `main` of a new `hitsum-site` repo, behind Cloudflare DNS | Existing, proven setup |
| Theme | Dark only | Matches the app; one theme to maintain |
| Fonts | System stack + `ui-monospace` / SF Mono for numerals | No web font downloads |
| Hero media | App Store screenshot #1 in a phone frame | Real footage doesn't exist yet; the layout accepts a looping video later without changes |
| Analytics | None in the page; optional Cloudflare Web Analytics toggled in the dashboard | No cookies, no consent banner, consistent with the privacy policy |
| Pricing | Describe Free vs Premium features; no prices | Owner decision |

## 4. Site map

```
/                 Home
/setup/           Setup guide
/support/         Support
/privacy/         Privacy policy (HitSum)
/404.html         Not found
```

Every page shares:
- **Header:** HitSum wordmark (links to `/`) · Setup · Support.
- **Footer:** © 2026 Kiki Gadgets Ltd · Privacy · Support · Credits line (OpenStreetMap ODbL attribution; Unsplash credits only if those photos are used on the site).

## 5. Pages

### 5.1 Home (`/`)

The sections, in order:

1. **Hero**
   - H1: "Your iPhone is the launch monitor."
   - Subhead: "Ball speed, carry and a traced flight from every swing. Nothing to buy, pair or charge."
   - **CTA block** (see §7): before release, a pill reading "Coming to the App Store · Nov 7"; after release, Apple's official "Download on the App Store" badge.
   - Visual: `design/appstore/upload/iphone/1.png`, shown as-is (it already includes its caption and frame) or cropped to the device area. Pick whichever reads better at phone width during the build.
2. **Features.** Three blocks, each a screenshot plus a heading and two lines of copy taken from the App Store description:
   - *Launch monitor*: ball speed, launch, carry, total, apex and hang time; results read aloud.
   - *Shot tracer*: film a swing, tap the ball, share a clip with the flight line and carry.
   - *See it land and know your bag*: 3D range with greens from 50 to 350 yd, plus per-club carry analysis.
   - On desktop, rows alternate image left/right. On phones they stack.
3. **Honest numbers.** A short strip: lime values are measured from high-speed video and grey "EST" values are estimated (for example, total and apex assume typical spin). It contains no percentages.
4. **Set up in 30 seconds.** Three numbered steps that mirror the in-app tutorial cards:
   1. Secure the phone 6–10 ft from the ball, side-on to the target line, upright, with the ball near the bottom of the frame.
   2. Tap the ball on screen and wait for "Ready".
   3. Hit, and hear your numbers.

   Followed by a link to `/setup/`.
5. **Free vs Premium.** Two columns:
   - *Free:* launch monitor for 15 measured shots a day, the shot tracer, and the review of today's session.
   - *Premium:* unlimited shots, full shot history, per-club analysis, exports without a watermark, and hosting a Join session. Monthly or yearly, and yearly includes a 7-day free trial. No prices.
6. **FAQ.** Uses native `<details>`/`<summary>`.
   - Which iPhones work? 12 or later for the launch monitor; iPads and older iPhones on iOS 17.2+ can watch a Join session.
   - Do I need slow motion? Yes, 240 fps.
   - Does it work indoors? Yes, 8–10 ft from a net or screen.
   - How accurate is it? Measured from high-speed video; carry assumes typical spin. No percentages.
   - Does it measure spin? No. Spin is estimated.
   - What about altitude? HitSum uses the phone's barometer.
   - Is there an Android version? Not yet.
   - What's free? Short answer, then a link to the Free vs Premium section.
7. **Closing CTA.** Repeats the hero CTA block.

### 5.2 Setup guide (`/setup/`)

Sections with in-page anchors so Support and the FAQ can deep-link:

- `#launch-monitor`: placement (distance, side-on, upright, ball low in frame), 240 fps slow motion, light (bright and even; shade hurts detection), indoors (8–10 ft), tapping the ball, and lime vs grey.
- `#shot-tracer`: hold still and don't follow the ball; record, then mark the ball under the crosshair; check, then trace; sharing.
- `#join`: hosting (Premium) vs watching (free; iPad and older iPhones on 17.2+).
- `#troubleshooting`: "Missed" shots, ball not found, numbers look off. Each item gets a one-line cause and fix.

Illustrations use existing screenshots for now. The page reserves a slot for each of the six planned tutorial photos (`securedPhone`, `tapTheBall`, `measuredAndEstimated`, `holdStill`, `recordThenMark`, `checkThenTrace`) so they can drop in later. The copy must match the in-app tutorial cards. Where they disagree, the app is the source of truth.

### 5.3 Support (`/support/`)

- Contact: `support@kikigadgetsltd.com` as a `mailto:` link. No form.
- Top three setup tips, with a link to `/setup/`.
- Subscriptions: manage or cancel in Apple ID settings (with a link to Apple's instructions), restore purchases, free trial terms.
- Account: Sign in with Apple is optional, and how to delete your account.
- Requirements and known limits.

### 5.4 Privacy (`/privacy/`)

The current HitSum policy (`golftrace/docs/legal/privacy.md`, effective 2026-09-25) rendered as HTML. The kikigadgetsltd.com copy stays live and unchanged. Add a line to `RELEASE.md` to keep both in sync, or later replace the kiki page with a redirect.

### 5.5 404

The brand header, a single line, and links to Home and Setup.

## 6. Visual design

- **Colors** (sampled from the App Store screenshots) as CSS custom properties:
  - `--bg: #121315`
  - `--surface: #1b1d1f`, for cards and FAQ items
  - `--text: #ffffff`
  - `--text-muted: #9aa0a6`, for grey "estimated"-style text. Must meet 4.5:1 contrast on `--bg`.
  - `--lime: #c8f542`, for accents, headings' emphasis and the CTA pill. Never used for body text on white.
- **Type:**
  - `system-ui, -apple-system, …` for text.
  - `ui-monospace, "SF Mono", Menlo, monospace` for stat numerals.
  - Fluid heading sizes with `clamp()`.
- **Layout:**
  - Mobile-first, single column, 16px side gutters, max content width around 1100px.
  - Feature rows go two-column at ≥768px.
  - No horizontal scroll at 320px.
- **Images:**
  - Convert the needed App Store PNGs to WebP at two widths (around 480 and 960) with PNG fallback via `<picture>`.
  - Set `width`/`height` attributes to avoid layout shift.
  - The hero image loads eagerly; everything else uses `loading="lazy"`.
- **Motion:** none required. Respect `prefers-reduced-motion` if any is added.
- **Icons:** favicon (32px PNG + SVG if available), `apple-touch-icon` 180px, both from `AppIcon-comet-1024.png`.

## 7. Release-day CTA switch

Each page contains the CTA block in exactly one marked region:

```html
<!-- CTA:BEGIN -->
<span class="cta-pill">Coming to the App Store · Nov 7</span>
<!-- CTA:END -->
```

On release day, replace each region with Apple's official badge SVG linked to the App Store URL. Also add `<meta name="apple-itunes-app" content="app-id=…">` to every page's `<head>`.

`RELEASE.md` in the repo lists every step:
1. Swap the CTA regions.
2. Add the Smart App Banner tag.
3. Add the App Store URL to the JSON-LD.
4. Update the App Store Connect Support URL → `https://hitsum.app/support/` and Privacy URL → `https://hitsum.app/privacy/`, submitted alongside the next app version or as a metadata edit where Apple allows it.
5. Set `AppLink.url` in the app (tracked in the app repo, not here).

## 8. SEO and sharing

- A unique `<title>` and meta description per page.
- `<link rel="canonical">` to the `https://hitsum.app/...` URL.
- Open Graph + Twitter card tags. The image is `design/appstore/upload/header-16x9.png`, resized to 1200×630 if needed.
- `SoftwareApplication` JSON-LD on Home: name, operatingSystem "iOS", applicationCategory "SportsApplication", offers price 0. **No** aggregateRating until real ratings exist.
- `sitemap.xml` (four pages) and `robots.txt` pointing to it.
- Semantic HTML: one H1 per page, landmark elements, and alt text on every screenshot that describes what the screen shows.

## 9. Repository layout

```
hitsum-site/
  CNAME                 # hitsum.app
  .nojekyll
  index.html
  setup/index.html
  support/index.html
  privacy/index.html
  404.html
  style.css
  assets/
    img/                # webp + png screenshots, icon, og image
    badges/             # Apple App Store badge (added on release)
  robots.txt
  sitemap.xml
  RELEASE.md
  README.md             # how to edit, preview, deploy
  docs/superpowers/specs/   # this file
```

No JavaScript is required. If any is added later, it goes in a single deferred file.

## 10. Hosting and DNS setup

1. Create the GitHub repo `hitsum-site` and push `main`. Enable Pages from `main` / root. Custom domain `hitsum.app`, with "Enforce HTTPS" on.
2. **Cloudflare, hitsum.app:**
   - Apex `A`/`AAAA` records to GitHub Pages IPs, and `www` CNAME to `<user>.github.io`.
   - Start DNS-only (grey cloud) until GitHub issues the certificate, then optionally proxy.
   - SSL mode "Full".
3. **Cloudflare, hitsumgolf.com:** proxied placeholder records, plus a Redirect Rule: all requests → `https://hitsum.app${path}`, 301, keep the query string.
4. **Cloudflare, `www.hitsum.app`:** redirect to the apex.

These steps happen in the owner's GitHub and Cloudflare accounts. The implementation plan lists them as manual steps for the owner, with exact values.

## 11. Testing

Before announcing the site:

- **Visual:** every page at 375px, 768px and 1280px wide in a browser. Nothing overflows, no horizontal scroll, and FAQ items open and close.
- **Links:** a script or crawler confirms no broken internal links or missing images.
- **Lighthouse** (mobile) on Home and Setup: Performance, Accessibility and SEO ≥ 90.
- **Copy review:** no accuracy percentages, no monitor comparisons, no prices, no Android implication, and setup steps match the in-app cards.
- **Live checks** after DNS:
  - `https://hitsum.app` serves with a valid certificate.
  - `http://` redirects to `https://`.
  - `hitsumgolf.com/support/` 301s to `hitsum.app/support/`.
  - `www` variants redirect.

## 12. Out of scope (v1)

These can each be added later without restructuring:

- Email signup (pre-launch list or Android waitlist)
- Press kit page and zip
- `apple-app-site-association` and a Join-link fallback page
- Hero video (layout already accepts it)
- Blog or additional guides
- Light theme
- Localization
