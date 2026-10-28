"""One-shot image pipeline: turns the golftrace repo's raw screenshots, icon
and wordmark into the web images in assets/img. Outputs are committed, so
this only needs re-running when a source changes.

    python3 tools/build_images.py
"""
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

GOLFTRACE = Path.home() / "AndroidStudioProjects/golftrace"
SRC = GOLFTRACE / "design"
OUT = Path(__file__).resolve().parent.parent / "assets/img"

SHOTS = {
    "run": "appstore/raw/iphone/1-run.png",
    "analysis": "appstore/raw/device/analysis.png",
    "hole": "appstore/raw/device/hole.png",
    "trace": "appstore/raw/device/trace.png",
    "arcs": "appstore/raw/device/arcs.png",
}
WIDTHS = (480, 960)

# App Store preview recordings -> silent loops for the site.
PREVIEWS = {
    "hole": "appstore/upload/preview/iphone-preview-1.mp4",
    "analysis": "appstore/upload/preview/iphone-preview-2.mp4",
}
VIDEO_OUT = OUT.parent / "video"

# The setup Short (also on YouTube as DiPGG06o8gQ). The loop keeps 0-5.0 s
# (setting up) and 10.5 s-end (swing, number, the app calling the distance),
# cutting the walk to the ball. Audio stays for the page's "Sound on" button.
SETUP_SOURCE = Path.home() / "Documents/hitsum1-short.mp4"
SETUP_KEEP = ((0.0, 5.0), (10.5, None))
SETUP_POSTER_AT = 4.5  # in the cut: phone mounted and shaded, "Ready", ball in view


def resized(im, width):
    return im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)


def cover(im, size):
    """Scale `im` to cover `size`, then center-crop to it."""
    w, h = size
    scale = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    left, top = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((left, top, left + w, top + h))


def build_previews() -> None:
    """640px-wide H.264, no audio, faststart; poster is the first frame."""
    VIDEO_OUT.mkdir(parents=True, exist_ok=True)
    for stem, rel in PREVIEWS.items():
        clip = VIDEO_OUT / f"preview-{stem}.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(SRC / rel),
                        "-an", "-vf", "scale=640:-2", "-c:v", "libx264", "-profile:v", "high",
                        "-pix_fmt", "yuv420p", "-crf", "28", "-preset", "slow",
                        "-movflags", "+faststart", str(clip)], check=True)
        poster(clip, 0)


# Screen recording of tracing a shot. Keeps: the impact question, dragging the
# magnifier onto the ball, dragging the path's end to the landing spot, and
# the finished trace playing. Cuts spinners, the long correction stretch, the
# "Couldn't follow the ball" message and Control Center at the end.
TRACE_SOURCE = Path.home() / "Downloads/DA0025FB-C240-4A65-94DE-62A466F8F978.MP4"
TRACE_KEEP = ((2.5, 4.0), (4.6, 7.6), (18.0, 20.5), (23.8, 30.4))
TRACE_POSTER_AT = 12.4  # in the cut: the finished trace line over the follow-through
STATUS_BAR_H = 165  # rows above the app's content in a 3x recording
POSTER_WIDTH = 480


def clean_bar(width: int) -> Path:
    """A 9:41 status bar `width` wide, like the App Store screenshots: the
    simulator's left and right clusters from 1-run.png on the app background."""
    ref = Image.open(SRC / "appstore/raw/iphone/1-run.png").convert("RGB")
    bar = Image.new("RGB", (width, STATUS_BAR_H), (0x14, 0x13, 0x16))
    bar.paste(ref.crop((0, 0, 400, 160)), (0, 0))
    bar.paste(ref.crop((ref.width - 400, 0, ref.width, 160)), (width - 400, 0))
    out = VIDEO_OUT / "_bar.png"
    bar.save(out)
    return out


def cut_silent(source: Path, keep, out: Path, overlay: Path) -> None:
    """Join the `keep` spans of `source` (no audio), lay `overlay` over the top,
    and scale to 640 wide at 30 fps."""
    parts = "".join(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];" for i, (a, b) in enumerate(keep))
    joins = "".join(f"[v{i}]" for i in range(len(keep)))
    graph = f"{parts}{joins}concat=n={len(keep)}:v=1:a=0[j];[j][1:v]overlay=0:0,fps=30,scale=640:-2[v]"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(source), "-i", str(overlay),
                    "-filter_complex", graph, "-map", "[v]", "-an",
                    "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "26",
                    "-preset", "slow", "-movflags", "+faststart", str(out)], check=True)


def poster(clip: Path, at: float) -> None:
    """The frame at `at` seconds as a light WebP next to the clip. Posters can't be
    lazy-loaded, so they're kept small: 480 wide covers the 320px display at 1.5x."""
    frame = clip.with_suffix(".png")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(at), "-i", str(clip),
                    "-frames:v", "1", str(frame)], check=True)
    resized(Image.open(frame).convert("RGB"), POSTER_WIDTH).save(clip.with_suffix(".webp"), quality=60)
    frame.unlink()


def build_trace_clip() -> None:
    bar = clean_bar(1180)
    clip = VIDEO_OUT / "trace-steps.mp4"
    cut_silent(TRACE_SOURCE, TRACE_KEEP, clip, overlay=bar)
    bar.unlink()
    poster(clip, TRACE_POSTER_AT)


def build_setup_loop() -> None:
    parts, inputs = [], []
    for i, (start, end) in enumerate(SETUP_KEEP):
        span = f"{start}:{end}" if end is not None else f"start={start}"
        parts.append(f"[0:v]trim={span},setpts=PTS-STARTPTS[v{i}];"
                     f"[0:a]atrim={span},asetpts=PTS-STARTPTS[a{i}];")
        inputs.append(f"[v{i}][a{i}]")
    graph = "".join(parts) + "".join(inputs) + f"concat=n={len(SETUP_KEEP)}:v=1:a=1[v][a]"
    clip = VIDEO_OUT / "setup-loop.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(SETUP_SOURCE),
                    "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
                    "-crf", "26", "-preset", "slow", "-c:a", "aac", "-b:a", "96k",
                    "-movflags", "+faststart", str(clip)], check=True)
    poster(clip, SETUP_POSTER_AT)


# The bag-mount kit: phone holder clamped to the bag, mini umbrella above.
# Cropped (in source pixels) to leave out the headcover's team logo.
KIT_SOURCE = Path.home() / "Downloads/PXL_20261010_220955627.PORTRAIT.jpg"
KIT_CROP = (0, 205, 2388, 4417)
FONTS = GOLFTRACE / "ios/GolfTraceApp/GolfTraceApp/Theme/Fonts"
LIME, INK, WHITE = (200, 245, 66), (18, 19, 21), (236, 237, 238)
# (title, detail, pill top-left, point on the photo), in the 960-wide output
KIT_CALLOUTS = (
    ("Mini umbrella", "Shade, less glare", (24, 540), (560, 440)),
    ("Phone holder", "Clamps to your bag", (24, 1010), (812, 1330)),
)


def callout(im: Image.Image, title: str, detail: str, at, target) -> None:
    d = ImageDraw.Draw(im, "RGBA")
    # Sized to stay readable when the photo shows ~335px wide on a phone.
    big_px, small_px = 50, 38
    big = ImageFont.truetype(str(FONTS / "IBMPlexSans-SemiBold.otf"), big_px)
    small = ImageFont.truetype(str(FONTS / "IBMPlexSans-Medium.otf"), small_px)
    pad, gap = 24, 8
    w = int(max(d.textlength(title, font=big), d.textlength(detail, font=small))) + 2 * pad
    h = big_px + gap + small_px + 2 * pad + 8
    x, y = at
    anchor = (x + w, y + h // 2)
    for width, colour in ((10, (*INK, 200)), (4, (*LIME, 255))):  # dark halo under the lime line
        d.line([anchor, target], fill=colour, width=width)
    for r, colour in ((16, (*INK, 200)), (11, (*LIME, 255)), (5, (*INK, 255))):
        d.ellipse([target[0] - r, target[1] - r, target[0] + r, target[1] + r], fill=colour)
    d.rounded_rectangle([x, y, x + w, y + h], radius=22, fill=(*INK, 225), outline=(*LIME, 255), width=3)
    d.text((x + pad, y + pad - 4), title, font=big, fill=LIME)
    d.text((x + pad, y + pad + big_px + gap), detail, font=small, fill=WHITE)


def build_kit_photo() -> None:
    """Crop, annotate and save the kit photo. Saved fresh, so no EXIF or other
    metadata from the camera comes along."""
    im = Image.open(KIT_SOURCE).convert("RGB").crop(KIT_CROP)
    im = resized(im, 960)
    for title, detail, at, target in KIT_CALLOUTS:
        callout(im, title, detail, at, target)
    clean = Image.new("RGB", im.size)
    clean.paste(im)
    clean.save(OUT / "kit-960.jpg", quality=82, optimize=True, progressive=True)
    clean.save(OUT / "kit-960.webp", quality=80)
    resized(clean, 480).save(OUT / "kit-480.webp", quality=80)


def main() -> None:
    # Real-device captures get the simulator's clean 9:41 status bar, exactly
    # as the App Store screenshots do.
    sys.path.insert(0, str(GOLFTRACE / "tools/appstore"))
    from frame import clean_status_bar

    OUT.mkdir(parents=True, exist_ok=True)
    for stem, rel in SHOTS.items():
        shot = Image.open(SRC / rel).convert("RGB")
        if "/device/" in rel:
            shot = clean_status_bar(shot)
        for width in WIDTHS:
            resized(shot, width).save(OUT / f"shot-{stem}-{width}.webp", quality=82)
        resized(shot, 960).save(OUT / f"shot-{stem}-960.png", optimize=True)

    svg = (SRC / "photos/export/wordmark/svg/HitSum-Wordmark-Small.svg").read_text()
    svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.DOTALL)
    svg = svg.replace(' xmlns:c2pa="http://c2pa.org/manifest"', "")
    (OUT / "wordmark.svg").write_text(svg)

    icon = Image.open(SRC / "icons/AppIcon-comet-1024.png").convert("RGB")
    icon.resize((180, 180), Image.LANCZOS).save(OUT / "icon-180.png", optimize=True)
    icon.resize((32, 32), Image.LANCZOS).save(OUT / "favicon-32.png", optimize=True)

    header = Image.open(SRC / "appstore/upload/header-16x9.png").convert("RGB")
    cover(header, (1200, 630)).save(OUT / "og.png", optimize=True)

    build_previews()
    build_setup_loop()
    build_trace_clip()
    build_kit_photo()


if __name__ == "__main__":
    main()
