import json
import re
import subprocess
import unittest
from pathlib import Path

from PIL import Image

from tools.sitecheck import check_page, check_site, parse_page

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


def content_images(p):
    """<img>s other than the header wordmark and the App Store badge."""
    return [i for i in p.images if i["tag"] == "img"
            and "wordmark" not in i.get("src", "") and "/assets/badges/" not in i.get("src", "")]


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

    def test_preview_clips_are_small_silent_640_wide(self):
        for stem in ["hole", "analysis"]:
            clip = ROOT / f"assets/video/preview-{stem}.mp4"
            self.assertLess(clip.stat().st_size, 2_000_000, clip.name)
            probe = json.loads(subprocess.run(
                ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(clip)],
                capture_output=True, text=True, check=True).stdout)["streams"]
            self.assertEqual([st["codec_type"] for st in probe], ["video"], clip.name)
            self.assertEqual((probe[0]["codec_name"], probe[0]["width"]), ("h264", 640))
            self.assertTrue((ROOT / f"assets/video/preview-{stem}.webp").is_file())

    def test_setup_loop_is_the_cut_with_sound(self):
        clip = ROOT / "assets/video/setup-loop.mp4"
        self.assertLess(clip.stat().st_size, 3_000_000)
        info = json.loads(subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(clip)],
            capture_output=True, text=True, check=True).stdout)
        self.assertEqual(sorted(st["codec_type"] for st in info["streams"]), ["audio", "video"])
        # 0-5.0 s setup + 10.5-15.6 s swing and spoken distance; the walk to the ball is cut.
        self.assertAlmostEqual(float(info["format"]["duration"]), 10.1, delta=0.15)
        self.assertTrue((ROOT / "assets/video/setup-loop.webp").is_file())

    def test_trace_clip_is_the_silent_cut(self):
        clip = ROOT / "assets/video/trace-steps.mp4"
        self.assertLess(clip.stat().st_size, 2_000_000)
        info = json.loads(subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(clip)],
            capture_output=True, text=True, check=True).stdout)
        self.assertEqual([st["codec_type"] for st in info["streams"]], ["video"])
        self.assertEqual(info["streams"][0]["width"], 640)
        # 2.5-4.0 + 4.6-7.6 + 18.0-20.5 + 23.8-30.4 s of the recording
        self.assertAlmostEqual(float(info["format"]["duration"]), 13.6, delta=0.15)
        self.assertTrue((ROOT / "assets/video/trace-steps.webp").is_file())

    def test_posters_are_light(self):
        # Posters can't be lazy-loaded: every one downloads with the hero screenshot.
        # Four full-size posters (190 KB) pushed Home's mobile LCP from 2.2 s to 2.6 s.
        posters = sorted((ROOT / "assets/video").glob("*.webp"))
        self.assertEqual(len(posters), 4)
        for f in posters:
            self.assertEqual(Image.open(f).width, 480, f.name)
        self.assertLess(sum(f.stat().st_size for f in posters), 100_000)

    def test_kit_photo_outputs_have_no_metadata(self):
        for f in ["kit-480.webp", "kit-960.webp", "kit-960.jpg"]:
            im = Image.open(ROOT / "assets/img" / f)
            self.assertEqual(len(im.getexif()), 0, f)
            self.assertNotIn("exif", im.info, f)
        self.assertEqual(Image.open(ROOT / "assets/img/kit-960.jpg").width, 960)

    def test_motion_script_respects_reduced_motion(self):
        js = (ROOT / "assets/js/motion.js").read_text()
        self.assertIn("prefers-reduced-motion: reduce", js)
        self.assertIn("IntersectionObserver", js)

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

    def test_anchor_jumps_are_instant(self):
        # Smooth scrolling stalled /setup/#troubleshooting deep links in an unfocused
        # Chromium pane (scrollY stayed 0); instant jumps always land.
        self.assertNotIn("scroll-behavior: smooth", (ROOT / "style.css").read_text())

    def test_every_page_has_an_install_cta(self):
        # Spec §7: each page carries the CTA block, so visitors landing anywhere can install.
        for rel in ["index.html", "setup/index.html", "support/index.html", "privacy/index.html", "404.html"]:
            self.assertGreaterEqual(page(rel).cta_begin, 1, rel)

    def test_cta_pill_wraps_on_narrow_screens(self):
        # At 320px the nowrap pill (302px) was wider than the 288px column and ate the right gutter.
        css = (ROOT / "style.css").read_text()
        narrow = re.search(r"@media \(max-width: 359px\) \{(.*?)\n\}", css, re.DOTALL)
        self.assertIsNotNone(narrow)
        self.assertRegex(narrow.group(1), r"\.cta-pill \{[^}]*white-space: normal")

    def test_404_page_passes(self):
        self.assertEqual(page_problems("404.html"), [])


SETUP_CLIP = "/assets/video/setup-loop.mp4"
SETUP_ON_YOUTUBE = "https://www.youtube.com/shorts/DiPGG06o8gQ"


def setup_clips(p):
    return [v for v in p.videos if v["sources"] == [SETUP_CLIP]]


TRACE_CLIP = "/assets/video/trace-steps.mp4"


def assert_trace_clip(test, p, section):
    """The silent tracer walkthrough replaces the still tracer screenshot in `section`."""
    clips = [v for v in p.videos if v["sources"] == [TRACE_CLIP]]
    test.assertEqual(len(clips), 1)
    test.assertEqual(clips[0]["_section"], section)
    test.assertNotIn("data-sound", clips[0])
    test.assertFalse(any("shot-trace" in i.get("src", "") for i in p.images if i["tag"] == "img"))


def assert_setup_clip(test, p, section):
    """The self-hosted setup loop, in `section`, with its sound button and YouTube link."""
    clips = setup_clips(p)
    test.assertEqual(len(clips), 1)
    test.assertEqual(clips[0]["_section"], section)
    test.assertIn("data-sound", clips[0])
    test.assertIn(SETUP_ON_YOUTUBE, p.links)
    test.assertEqual(p.iframes, [])  # no YouTube player: the site makes no third-party requests
    test.assertIn("/assets/js/motion.js", p.scripts)


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
        self.assertEqual(self.p.details_count, 7)
        for i in ["iphones", "indoors", "accuracy", "spin", "altitude", "android", "free"]:
            self.assertIn(f"faq-{i}", self.p.ids)
        # Every iPhone the launch monitor supports films slow motion, so no FAQ for it.
        self.assertNotIn("faq-slowmo", self.p.ids)

    def test_setup_step_mentions_bag_mount(self):
        self.assertIn("Clip your phone to your bag", self.p.text)
        self.assertIn("no tripod needed", self.p.text)

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

    def test_setup_video_section_comes_right_after_the_hero(self):
        html = (ROOT / "index.html").read_text()
        order = re.findall(r'<section[^>]*\bid="([^"]+)"', html)
        self.assertEqual(order, ["setup-steps", "features", "honest", "free-premium", "faq"])
        self.assertLess(html.index('class="wrap hero"'), html.index('id="setup-steps"'))

    def test_trace_clip_in_features(self):
        assert_trace_clip(self, self.p, "features")

    def test_setup_clip_in_setup_steps(self):
        assert_setup_clip(self, self.p, "setup-steps")

    def test_preview_clips_in_see_it_land_row(self):
        previews = [v for v in self.p.videos if v["sources"][0].startswith("/assets/video/preview-")]
        self.assertEqual([v["sources"][0] for v in previews],
                         ["/assets/video/preview-hole.mp4", "/assets/video/preview-analysis.mp4"])
        self.assertTrue(all(v["_section"] == "features" for v in previews))
        self.assertIn("/assets/js/motion.js", self.p.scripts)

    def test_links_to_setup(self):
        self.assertIn("/setup/", self.p.links)

    def test_hero_image_eager_rest_lazy(self):
        imgs = content_images(self.p)
        self.assertNotEqual(imgs[0].get("loading"), "lazy")
        for img in imgs[1:]:
            self.assertEqual(img.get("loading"), "lazy", img.get("src"))

    def test_release_badge_does_not_change_which_image_is_the_hero(self):
        badge = ('<a href="https://apps.apple.com/app/id1"><img src="/assets/badges/app-store-badge.svg" '
                 'alt="Download on the App Store" width="120" height="40"></a>')
        html = re.sub(r"<!-- CTA:BEGIN -->.*?<!-- CTA:END -->", f"<!-- CTA:BEGIN -->{badge}<!-- CTA:END -->",
                      (ROOT / "index.html").read_text(), flags=re.DOTALL)
        imgs = content_images(parse_page(html, "index.html"))
        self.assertIn("shot-run", imgs[0]["src"])


class Setup(unittest.TestCase):
    def setUp(self):
        self.p = page("setup/index.html")

    def test_setup_passes_page_check(self):
        self.assertEqual(page_problems("setup/index.html"), [])

    def test_setup_anchors(self):
        want = {"launch-monitor", "shot-tracer", "join", "troubleshooting",
                "photo-securedPhone", "photo-tapTheBall", "photo-measuredAndEstimated"}
        self.assertLessEqual(want, self.p.ids)

    def test_tutorial_titles_verbatim(self):
        for title in ["Set up directly behind the ball", "Select your hitting area",
                      "Lime is measured. Grey is estimated."]:
            self.assertIn(title, self.p.text)

    def test_distance_copy(self):
        self.assertIn("7.5 ft (2.3 m)", self.p.text)
        self.assertIn("two driver lengths", self.p.text)
        self.assertIn("A foot off at 7.5 ft puts every number off by", self.p.text)
        self.assertIn("eighth", self.p.text)

    def test_troubleshooting_items(self):
        for s in ["Too dark", "Not the ball", "sideways", "Missed"]:
            self.assertIn(s, self.p.text)

    def test_title_and_h1(self):
        self.assertEqual(self.p.h1s, ["Set up HitSum"])

    def test_what_you_need(self):
        self.assertIn("what-you-need", self.p.ids)
        self.assertIn("No tripod needed", self.p.text)
        amazon = [h for h in self.p.links if h.startswith("https://www.amazon.com/s?k=")]
        self.assertEqual(len(amazon), 2)

    def test_kit_photo_fills_the_secured_phone_slot(self):
        html = (ROOT / "setup/index.html").read_text()
        slot = html[html.index('id="photo-securedPhone"'):]
        slot = slot[:slot.index("</figure>")]
        self.assertIn("/assets/img/kit-960.jpg", slot)
        self.assertNotIn("photo-slot", slot)

    def test_trace_clip_in_shot_tracer_section(self):
        assert_trace_clip(self, self.p, "shot-tracer")

    def test_setup_clip_in_launch_monitor_section(self):
        assert_setup_clip(self, self.p, "launch-monitor")


class Support(unittest.TestCase):
    def setUp(self):
        self.p = page("support/index.html")

    def test_support_passes_page_check(self):
        self.assertEqual(page_problems("support/index.html"), [])

    def test_contact_mailto(self):
        self.assertIn("mailto:support@kikigadgetsltd.com", self.p.links)
        self.assertIn("support@kikigadgetsltd.com", self.p.text)

    def test_deep_links(self):
        for href in ["/setup/#launch-monitor", "/setup/#troubleshooting", "/#free-premium"]:
            self.assertIn(href, self.p.links)

    def test_subscription_help(self):
        # The app's label (SettingsView.swift) is "Restore purchases".
        self.assertIn("Restore purchases", self.p.text)
        self.assertIn("24 hours", self.p.text)
        self.assertTrue(any(h.startswith("https://support.apple.com/") for h in self.p.links))

    def test_account_deletion(self):
        self.assertIn("Delete account", self.p.text)

    def test_h1(self):
        self.assertEqual(self.p.h1s, ["HitSum support"])


SRC_MD = Path.home() / "AndroidStudioProjects/golftrace/docs/legal/privacy.md"


class Privacy(unittest.TestCase):
    def setUp(self):
        self.p = page("privacy/index.html")

    def test_privacy_passes_page_check(self):
        self.assertEqual(page_problems("privacy/index.html"), [])

    @unittest.skipUnless(SRC_MD.exists(), "golftrace repo not on this machine")
    def test_headings_match_source(self):
        want = [line[3:].strip() for line in SRC_MD.read_text().splitlines() if line.startswith("## ")]
        self.assertEqual(self.p.h2s, want)

    def test_effective_date(self):
        self.assertIn("September 25, 2026", self.p.text)

    def test_h1(self):
        self.assertEqual(self.p.h1s, ["HitSum Privacy Policy"])

    def test_publisher(self):
        self.assertIn("Kiki Gadgets Ltd", self.p.text)


class WholeSite(unittest.TestCase):
    def test_check_site_clean(self):
        self.assertEqual(check_site(ROOT), [])


if __name__ == "__main__":
    unittest.main()
