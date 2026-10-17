import tempfile
import unittest
from pathlib import Path

from tools.sitecheck import check_copy, check_page, check_site, parse_page

GOOD = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>T</title>
<meta name="description" content="A description that is long enough to pass the fifty character floor.">
<link rel="canonical" href="https://hitsum.app/setup/"><link rel="stylesheet" href="/style.css">
<meta property="og:title" content="t"><meta property="og:description" content="d">
<meta property="og:image" content="https://hitsum.app/assets/img/og.png"><meta property="og:url" content="https://hitsum.app/setup/">
<meta name="twitter:card" content="summary_large_image"></head>
<body><h1 id="top">Setup</h1><a href="/setup/#top">x</a></body></html>"""


def problems_for(html):
    """check_page on `html` saved as setup/index.html in a temp site root."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "setup").mkdir()
        (root / "setup/index.html").write_text(html)
        (root / "style.css").write_text("")
        return check_page(parse_page(html, "setup/index.html"), root)


def with_body(extra):
    return GOOD.replace("</body>", extra + "</body>")


class ParsePage(unittest.TestCase):
    def test_parse_page_extracts_fields(self):
        page = parse_page(GOOD, "setup/index.html")
        self.assertEqual(page.title, "T")
        self.assertEqual(page.canonical, "https://hitsum.app/setup/")
        self.assertEqual(page.h1s, ["Setup"])
        self.assertIn("top", page.ids)
        self.assertEqual(page.links, ["/setup/#top"])
        self.assertEqual(page.lang, "en")
        self.assertEqual(page.meta["og:title"], "t")

    def test_parse_page_collects_h2s(self):
        page = parse_page(with_body("<h2>One</h2><section><h2>Two <em>x</em></h2></section>"))
        self.assertEqual(page.h2s, ["One", "Two x"])


class CheckPage(unittest.TestCase):
    def test_good_page_has_no_problems(self):
        self.assertEqual(problems_for(GOOD), [])

    def test_two_h1s_are_reported(self):
        self.assertTrue(any("h1" in p for p in problems_for(with_body("<h1>Again</h1>"))))

    def test_missing_anchor_is_reported(self):
        self.assertTrue(any("#nope" in p for p in problems_for(with_body('<a href="/setup/#nope">n</a>'))))

    def test_directory_link_without_slash_is_reported(self):
        self.assertTrue(any("trailing slash" in p for p in problems_for(with_body('<a href="/setup">n</a>'))))

    def test_missing_link_target_is_reported(self):
        found = problems_for(with_body('<a href="/support/">s</a>'))
        self.assertTrue(any(p.startswith("link target missing") for p in found), found)

    def test_missing_image_file_is_reported(self):
        img = '<img src="/assets/img/x.png" alt="a" width="1" height="1">'
        self.assertTrue(any("x.png" in p for p in problems_for(with_body(img))))

    def test_image_without_alt_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "setup").mkdir()
            (root / "style.css").write_text("")
            (root / "a.png").write_bytes(b"")
            html = with_body('<img src="/a.png" width="1" height="1">')
            found = check_page(parse_page(html, "setup/index.html"), root)
        self.assertTrue(any("alt" in p for p in found), found)

    def test_script_tag_is_reported(self):
        self.assertTrue(any("script" in p for p in problems_for(with_body('<script src="/a.js"></script>'))))

    def test_unbalanced_cta_markers_are_reported(self):
        self.assertTrue(any("CTA" in p for p in problems_for(with_body("<!-- CTA:BEGIN --><span>c</span>"))))


class CheckCopy(unittest.TestCase):
    def test_copy_flags_percentage(self):
        self.assertEqual(check_copy("off by 13%"), ["percentage"])

    def test_copy_flags_r10_garmin_price_sideon(self):
        self.assertEqual(check_copy("matches an R10"), ["monitor comparison"])
        self.assertEqual(check_copy("like a Garmin"), ["monitor comparison"])
        self.assertEqual(check_copy("only $4.99"), ["price"])
        self.assertEqual(check_copy("stand side-on"), ["superseded placement wording"])

    def test_copy_allows_android_not_yet(self):
        self.assertEqual(check_copy("Is there an Android version? Not yet."), [])

    def test_copy_flags_android_claim(self):
        self.assertEqual(check_copy("Coming to Android soon."), ["android claim"])


class FinalReviewFixes(unittest.TestCase):
    def test_copy_checked_in_title_meta_alt_and_jsonld(self):
        title = GOOD.replace("<title>T</title>", "<title>99% accurate</title>")
        meta = GOOD.replace('content="d">', 'content="Only £4.99">')
        alt = with_body('<img src="/style.css" alt="Beats Garmin" width="1" height="1">')
        jsonld = with_body('<script type="application/ld+json">{"description": "side-on setup"}</script>')
        for html, want in [(title, "percentage"), (meta, "price"), (alt, "monitor comparison"),
                           (jsonld, "superseded placement wording")]:
            self.assertIn(want, problems_for(html), want)

    def test_copy_flags_variants(self):
        self.assertEqual(check_copy("only £4.99"), ["price"])
        self.assertEqual(check_copy("only €5"), ["price"])
        self.assertEqual(check_copy("29.99/yr"), ["price"])
        self.assertEqual(check_copy("off by 2 percent"), ["percentage"])
        self.assertEqual(check_copy("stand side on"), ["superseded placement wording"])
        self.assertEqual(check_copy("stand side\u2011on"), ["superseded placement wording"])
        for name in ["Rapsodo", "Trackman", "TrackMan", "True Carry", "Foresight", "SkyTrak", "Mevo"]:
            self.assertEqual(check_copy(f"better than {name}"), ["monitor comparison"], name)

    def test_text_seen_when_head_is_not_closed(self):
        page = parse_page("<html lang=en><head><title>t</title><body><p>99% accurate</p></body></html>")
        self.assertIn("99% accurate", page.text)

    def test_release_placeholder_is_reported(self):
        found = problems_for(with_body('<a href="APP_STORE_URL">Get it</a>'))
        self.assertTrue(any("placeholder" in p for p in found), found)
        found = problems_for(GOOD.replace("</head>", '<meta name="apple-itunes-app" content="app-id=APP_ID"></head>'))
        self.assertTrue(any("placeholder" in p for p in found), found)

    def test_relative_link_is_reported(self):
        found = problems_for(with_body('<a href="setup/#nope">x</a>'))
        self.assertTrue(any("root-relative" in p for p in found), found)

    def test_absolute_same_site_link_is_checked(self):
        found = problems_for(with_body('<a href="https://hitsum.app/setupp/">x</a>'))
        self.assertTrue(any(p.startswith("link target missing") for p in found), found)


class Iframes(unittest.TestCase):
    NOCOOKIE = ('<iframe src="https://www.youtube-nocookie.com/embed/abc" title="Setup video" '
                'loading="lazy" allowfullscreen></iframe>')

    def test_parse_page_collects_iframes(self):
        page = parse_page(with_body(self.NOCOOKIE))
        self.assertEqual(page.iframes[0]["src"], "https://www.youtube-nocookie.com/embed/abc")

    def test_privacy_enhanced_lazy_titled_iframe_passes(self):
        self.assertEqual(problems_for(with_body(self.NOCOOKIE)), [])

    def test_iframe_from_youtube_com_is_reported(self):
        html = with_body(self.NOCOOKIE.replace("www.youtube-nocookie.com", "www.youtube.com"))
        self.assertTrue(any("youtube-nocookie" in p for p in problems_for(html)))

    def test_iframe_without_title_is_reported(self):
        html = with_body(self.NOCOOKIE.replace(' title="Setup video"', ""))
        self.assertTrue(any("title" in p for p in problems_for(html)))

    def test_iframe_not_lazy_is_reported(self):
        html = with_body(self.NOCOOKIE.replace(' loading="lazy"', ""))
        self.assertTrue(any("lazy" in p for p in problems_for(html)))


class CheckSite(unittest.TestCase):
    def test_check_site_requires_cname_sitemap_robots(self):
        with tempfile.TemporaryDirectory() as d:
            found = " ".join(check_site(Path(d)))
        for word in ["CNAME", ".nojekyll", "robots", "sitemap", "index.html"]:
            self.assertIn(word, found)


if __name__ == "__main__":
    unittest.main()
