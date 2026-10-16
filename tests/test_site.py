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


if __name__ == "__main__":
    unittest.main()
