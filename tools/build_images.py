"""One-shot image pipeline: turns the golftrace repo's raw screenshots, icon
and wordmark into the web images in assets/img. Outputs are committed, so
this only needs re-running when a source changes.

    python3 tools/build_images.py
"""
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

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
        frame = VIDEO_OUT / f"preview-{stem}.png"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(clip),
                        "-frames:v", "1", str(frame)], check=True)
        Image.open(frame).convert("RGB").save(VIDEO_OUT / f"preview-{stem}.webp", quality=80)
        frame.unlink()


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
    frame = VIDEO_OUT / "setup-loop.png"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(SETUP_POSTER_AT), "-i", str(clip),
                    "-frames:v", "1", str(frame)], check=True)
    Image.open(frame).convert("RGB").save(VIDEO_OUT / "setup-loop.webp", quality=80)
    frame.unlink()


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


if __name__ == "__main__":
    main()
