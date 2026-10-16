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


class CheckSite(unittest.TestCase):
    def test_check_site_requires_cname_sitemap_robots(self):
        with tempfile.TemporaryDirectory() as d:
            found = " ".join(check_site(Path(d)))
        for word in ["CNAME", ".nojekyll", "robots", "sitemap", "index.html"]:
            self.assertIn(word, found)


if __name__ == "__main__":
    unittest.main()
