import re
import unittest
from pathlib import Path

from PIL import Image

from tools.sitecheck import check_page, parse_page

ROOT = Path(__file__).resolve().parent.parent

TOKENS = {
    "--bg": "#121315",
    "--surface": "#1b1d1f",
    "--text": "#ecedee",
    "--text-muted": "#9aa0a6",
    "--lime": "#c8f542",
}


def page(rel):
    return parse_page((ROOT / rel).read_text(), rel)


def page_problems(rel):
    """check_page minus missing link targets: pages link to pages built later,
    so link integrity is enforced by the whole-site check instead."""
    return [p for p in check_page(page(rel), ROOT) if not p.startswith("link target missing")]


def contrast(a, b):
    def lum(hex_):
        rgb = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    hi, lo = sorted([lum(a), lum(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def css_tokens():
    css = (ROOT / "style.css").read_text()
    return dict(re.findall(r"(--[a-z-]+)\s*:\s*(#[0-9a-fA-F]{6})", css))


class SiteFiles(unittest.TestCase):
    def test_image_outputs_exist(self):
        for stem in ["run", "analysis", "hole", "trace", "arcs"]:
            for f in [f"shot-{stem}-480.webp", f"shot-{stem}-960.webp", f"shot-{stem}-960.png"]:
                self.assertTrue((ROOT / "assets/img" / f).is_file(), f)
        self.assertEqual(Image.open(ROOT / "assets/img/og.png").size, (1200, 630))
        self.assertEqual(Image.open(ROOT / "assets/img/icon-180.png").size, (180, 180))
        self.assertEqual(Image.open(ROOT / "assets/img/favicon-32.png").size, (32, 32))

    def test_wordmark_has_no_c2pa_metadata(self):
        svg = (ROOT / "assets/img/wordmark.svg").read_text()
        self.assertNotIn("c2pa", svg)
        self.assertLess(len(svg.encode()), 6000)

    def test_css_tokens(self):
        tokens = {k: v.lower() for k, v in css_tokens().items()}
        for name, value in TOKENS.items():
            self.assertEqual(tokens.get(name), value, name)

    def test_muted_text_contrast(self):
        t = css_tokens()
        self.assertGreaterEqual(contrast(t["--text-muted"], t["--bg"]), 4.5)
        self.assertGreaterEqual(contrast(t["--text"], t["--bg"]), 7)

    def test_404_page_passes(self):
        self.assertEqual(page_problems("404.html"), [])


class Home(unittest.TestCase):
    def setUp(self):
        self.p = page("index.html")

    def test_home_passes_page_check(self):
        self.assertEqual(page_problems("index.html"), [])

    def test_hero(self):
        self.assertEqual(self.p.h1s, ["Your iPhone is the launch monitor."])
        self.assertIn("Nothing to buy, pair or charge.", self.p.text)

    def test_two_cta_regions_with_prelaunch_text(self):
        self.assertEqual((self.p.cta_begin, self.p.cta_end), (2, 2))
        self.assertEqual(self.p.text.count("Coming to the App Store · Nov 7"), 2)

    def test_sections_present(self):
        self.assertLessEqual({"features", "honest", "setup-steps", "free-premium", "faq"}, self.p.ids)

    def test_faq_items(self):
        self.assertEqual(self.p.details_count, 8)
        for i in ["iphones", "slowmo", "indoors", "accuracy", "spin", "altitude", "android", "free"]:
            self.assertIn(f"faq-{i}", self.p.ids)

    def test_setup_steps_match_app(self):
        for s in ["directly behind the ball", "7.5 ft (2.3 m)", "two driver lengths"]:
            self.assertIn(s, self.p.text)

    def test_estimated_values_named(self):
        self.assertIn("Carry and apex", self.p.text)

    def test_free_tier(self):
        self.assertIn("15 measured shots a day", self.p.text)
        self.assertIn("7-day free trial", self.p.text)

    def test_jsonld_software_application(self):
        apps = [j for j in self.p.jsonld if j.get("@type") == "SoftwareApplication"]
        self.assertEqual(len(apps), 1)
        app = apps[0]
        self.assertEqual(app["operatingSystem"], "iOS")
        self.assertEqual(app["applicationCategory"], "SportsApplication")
        self.assertEqual(app["offers"]["price"], "0")
        self.assertNotIn("aggregateRating", app)

    def test_links_to_setup(self):
        self.assertIn("/setup/", self.p.links)

    def test_hero_image_eager_rest_lazy(self):
        imgs = [i for i in self.p.images if i["tag"] == "img" and "wordmark" not in i.get("src", "")]
        self.assertNotEqual(imgs[0].get("loading"), "lazy")
        for img in imgs[1:]:
            self.assertEqual(img.get("loading"), "lazy", img.get("src"))


if __name__ == "__main__":
    unittest.main()
