"""
Generate the 4CE onboarding background.

    python 4ce/branding/make_onboarding_bg.py

Writes static/assets/onboarding-4ce.webp, a still image used behind the
first-run welcome screen. It replaces the upstream welcome video, which is an
impressionist painting of a farmhouse - fitting for "your AI home", wrong for a
workbench handling confidential refinery documents. The upstream asset is left
in place rather than overwritten.

A still rather than a video: it is a few hundred KB instead of ~2 MB, it cannot
fail to autoplay, and it costs nothing on a machine that is about to spend its
GPU on inference.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "static" / "assets" / "onboarding-4ce.webp"

W, H = 1920, 1080
TOP = (18, 23, 31)
BOTTOM = (7, 9, 13)
GRID = (255, 255, 255, 8)
GLOW = (86, 108, 140)


def gradient() -> Image.Image:
    base = Image.new("RGB", (1, H))
    pixels = base.load()
    for y in range(H):
        t = y / (H - 1)
        pixels[0, y] = tuple(round(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3))
    return base.resize((W, H), Image.BICUBIC)


def add_grid(canvas: Image.Image, step: int = 60) -> None:
    """A faint measured grid - a drawing sheet, not decoration."""
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for x in range(0, W, step):
        draw.line([(x, 0), (x, H)], fill=GRID, width=1)
    for y in range(0, H, step):
        draw.line([(0, y), (W, y)], fill=GRID, width=1)
    canvas.alpha_composite(overlay)


def add_glow(canvas: Image.Image) -> None:
    """A soft off-centre light so the flat gradient has some depth."""
    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    cx, cy, r = int(W * 0.68), int(H * 0.42), int(H * 0.52)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*GLOW, 46))
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(180)))


def add_mark(canvas: Image.Image) -> None:
    """The 4CE mark, large and quiet, sitting behind the copy."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("assets", HERE / "make_assets.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    mark = module.load_mark()
    size = int(H * 0.86)
    ratio = min(size / mark.width, size / mark.height)
    mark = mark.resize((round(mark.width * ratio), round(mark.height * ratio)), Image.LANCZOS)

    faded = mark.copy()
    faded.putalpha(mark.getchannel("A").point(lambda v: int(v * 0.16)))
    canvas.alpha_composite(faded, (int(W * 0.62), int(H * 0.5 - faded.height / 2)))


def main() -> None:
    canvas = gradient().convert("RGBA")
    add_grid(canvas)
    add_glow(canvas)
    add_mark(canvas)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(OUT, "WEBP", quality=88, method=6)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB, {W}x{H})")


if __name__ == "__main__":
    main()
