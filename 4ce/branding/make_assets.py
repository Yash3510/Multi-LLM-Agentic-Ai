"""
Generate the 4CE brand assets.

    python 4ce/branding/make_assets.py

Rewrites the icon, logo and splash images under static/ so the application
carries the 4CE identity rather than the upstream one. Re-runnable: it
regenerates every file from these definitions, so the assets always have a
source rather than being opaque binaries.

Requires Pillow, which is already a backend dependency.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
STATIC = ROOT / "static"

GRAPHITE = (13, 17, 23, 255)
WHITE = (255, 255, 255, 255)
AMBER = (240, 160, 32, 255)

FONT_CANDIDATES = [
    "C:/Windows/Fonts/seguibl.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def fit_font(draw, text, box_w, start):
    """Largest font whose rendered ink width fits box_w."""
    size = start
    while size > 8:
        font = load_font(size)
        left, _, right, _ = draw.textbbox((0, 0), text, font=font)
        if right - left <= box_w:
            return font
        size -= 4
    return load_font(8)


def draw_wordmark(canvas: Image.Image, colour, accent, margin_ratio=0.14, accent_bar=False):
    """Centre '4CE' with anchor-based placement so nothing collides."""
    size = canvas.size[0]
    draw = ImageDraw.Draw(canvas)
    box_w = int(size * (1 - 2 * margin_ratio))
    font = fit_font(draw, "4CE", box_w, int(size * 0.55))

    centre_y = size * (0.44 if accent_bar else 0.50)
    draw.text((size / 2, centre_y), "4CE", font=font, fill=colour, anchor="mm")

    if accent_bar:
        left, _, right, _ = draw.textbbox((0, 0), "4CE", font=font)
        bar_w = int((right - left) * 0.96)
        bar_h = max(3, int(size * 0.038))
        bar_x = (size - bar_w) // 2
        bar_y = int(size * 0.70)
        draw.rounded_rectangle(
            [bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
            radius=bar_h // 2,
            fill=accent,
        )
    return canvas


def tile(size: int) -> Image.Image:
    """The app icon: a graphite rounded square carrying the wordmark."""
    scale = 4
    big = size * scale
    canvas = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle([0, 0, big - 1, big - 1], radius=int(big * 0.22), fill=GRAPHITE)
    draw_wordmark(canvas, WHITE, AMBER, accent_bar=False)
    return canvas.resize((size, size), Image.LANCZOS)


def glyph(size: int, colour) -> Image.Image:
    """The splash lockup: wordmark only, transparent background."""
    scale = 4
    big = size * scale
    canvas = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw_wordmark(canvas, colour, AMBER, margin_ratio=0.08, accent_bar=True)
    return canvas.resize((size, size), Image.LANCZOS)


SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="113" fill="#0D1117"/>
  <text x="256" y="286" font-family="Segoe UI Black, Arial Black, Helvetica, sans-serif"
        font-size="196" font-weight="900" fill="#FFFFFF"
        text-anchor="middle" dominant-baseline="middle">4CE</text>
  <rect x="105" y="352" width="302" height="23" rx="11" fill="#F0A020"/>
</svg>
"""


def main() -> None:
    targets = {
        "static/favicon.png": tile(512),
        "static/static/favicon.png": tile(512),
        # The backend serves its own copy from STATIC_DIR. A production build
        # serves everything from here, so leaving it unbranded would quietly
        # revert the application to the upstream mark.
        "backend/open_webui/static/favicon.png": tile(512),
        "backend/open_webui/static/favicon-96x96.png": tile(96),
        "backend/open_webui/static/apple-touch-icon.png": tile(180),
        "backend/open_webui/static/logo.png": tile(500),
        "backend/open_webui/static/splash.png": glyph(500, GRAPHITE),
        "backend/open_webui/static/splash-dark.png": glyph(500, WHITE),
        "static/static/favicon-96x96.png": tile(96),
        "static/static/apple-touch-icon.png": tile(180),
        "static/static/web-app-manifest-192x192.png": tile(192),
        "static/static/web-app-manifest-512x512.png": tile(512),
        "static/static/logo.png": tile(500),
        "static/static/splash.png": glyph(500, GRAPHITE),
        "static/static/splash-dark.png": glyph(500, WHITE),
    }
    for relative, image in targets.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
        print(f"wrote {relative} {image.size}")

    ico = ROOT / "static/static/favicon.ico"
    tile(256).save(ico, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"wrote static/static/favicon.ico (multi-size)")

    svg = ROOT / "static/static/favicon.svg"
    svg.write_text(SVG, encoding="utf-8")
    print("wrote static/static/favicon.svg")


if __name__ == "__main__":
    main()
