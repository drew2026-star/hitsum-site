# Release day (Nov 7, 2026)

**App ID:** `6813047446`
**App Store URL:** use `https://apps.apple.com/app/id6813047446`, which always redirects to the
listing. The full listing URL is expected to be
`https://apps.apple.com/us/app/hitsum-golf-launch-monitor/id6813047446`, but its name part
follows the final App Store name, so prefer the short form. Check that both open once released.
Wherever a step below says `APP_STORE_URL` or `APP_ID`, use these values.

Do these in order once HitSum is live on the App Store.

1. **Swap the call to action.** There are six `<!-- CTA:BEGIN -->` … `<!-- CTA:END -->` regions:
   two in `index.html` (hero and closing) and one in the install band of `setup/`, `support/`,
   `privacy/` and `404.html`. Replace the "Coming to the App Store · Nov 7" pill in each with Apple's badge:
   - Download the official "Download on the App Store" badge (black, US English) from Apple's
     Marketing Resources site and save it as `assets/badges/app-store-badge.svg`.
   - Markup:
     ```html
     <!-- CTA:BEGIN -->
     <a href="APP_STORE_URL"><img src="/assets/badges/app-store-badge.svg" alt="Download on the App Store" width="120" height="40"></a>
     <!-- CTA:END -->
     ```
   - Change the "Free to download" note under the hero if you want different wording.
2. **Smart App Banner.** Add `<meta name="apple-itunes-app" content="app-id=APP_ID">` to the
   `<head>` of all five pages (`index.html`, `setup/`, `support/`, `privacy/`, `404.html`).
3. **JSON-LD.** In `index.html`'s `SoftwareApplication` block, add
   `"downloadUrl":"APP_STORE_URL","installUrl":"APP_STORE_URL"`.
4. **Test.** Run `python3 -m unittest discover -s tests` and `python3 tools/sitecheck.py`.
   `sitecheck` reports any `APP_STORE_URL` or `APP_ID` left unreplaced, so a forgotten placeholder
   can't ship. `Home.test_two_cta_regions_with_prelaunch_text` fails by design after step 1: change
   it to assert the real App Store link is in `links` and there are still two CTA regions.
   Everything else must pass.
   **If App Review slips past Nov 7,** change the date in all six pills (`grep -rn "Nov 7" --include=*.html .`).
5. **Publish.** Commit and push to `main`; GitHub Pages deploys in a minute or two.
6. **App Store Connect.** Set the Support URL to `https://hitsum.app/support/` and the Privacy
   Policy URL to `https://hitsum.app/privacy/` (with the next version, or as a metadata edit
   where Apple allows it).
7. **Privacy copies.** `kikigadgetsltd.com/privacy-hitsum.html` still holds the same policy.
   Keep both in sync when the policy changes, or replace that page with a link to
   `https://hitsum.app/privacy/`.
8. **App links.** Set `AppLink.url` in the golftrace app repo (tracked there, not here).
