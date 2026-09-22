"""
Generate the 4CE brand assets from the supplied logo mark.

    python 4ce/branding/make_assets.py

Rewrites the icon, logo and splash images under static/ and the backend's own
static directory, so the application carries the 4CE identity in both the
frontend and backend trees. Re-runnable: everything is derived from
`logo-source-onblack.jpeg`, so the assets always have a source rather than
being opaque binaries.

Why the black-background source rather than the cut-out PNG: the cut-out still
carries faint alpha across nearly the whole canvas, so its alpha channel cannot
be trimmed reliably. The mark is near-white on near-black, so luminance is a
cleaner mask and it preserves the silver gradient.

Requires Pillow, which is already a backend dependency.
"""

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = HERE / "logo-source-onblack.jpeg"

GRAPHITE = (13, 17, 23, 255)
WHITE = (255, 255, 255, 255)

# JPEG noise leaves the "black" background a little above zero. Lift the floor
# before using luminance as alpha, or the mark sits on a grey haze.
FLOOR = 42
GAIN = 2.4


def load_mark() -> Image.Image:
    """The mark as RGBA on a transparent ground, cropped to its content."""
    source = Image.open(SOURCE).convert("RGB")
    luminance = source.convert("L")

    # The artwork is monochrome silver on black, so luminance is the shape.
    # Rendering it as flat white with boosted alpha keeps the thin connecting
    # strands legible; left at their source brightness they wash out against
    # the graphite tile and only the bright crossing points survive.
    # Locate the mark from the bright crossing points only. Their bounding box
    # is stable across thresholds, whereas a low threshold drifts with JPEG
    # noise and returns most of the frame.
    core = luminance.point(lambda v: 255 if v > 150 else 0).getbbox()
    if core:
        pad = round(max(core[2] - core[0], core[3] - core[1]) * 0.07)
        box = (
            max(0, core[0] - pad),
            max(0, core[1] - pad),
            min(source.width, core[2] + pad),
            min(source.height, core[3] + pad),
        )
        source = source.crop(box)
        luminance = luminance.crop(box)

    alpha = luminance.point(lambda v: max(0, min(255, int((v - FLOOR) * GAIN))))
    mark = Image.new("RGBA", source.size, WHITE)
    mark.putalpha(alpha)
    return mark


def fit(mark: Image.Image, box: int) -> Image.Image:
    """Scale the mark to fill a square box, preserving aspect ratio.

    Unlike thumbnail() this scales up as well as down: the source mark is
    smaller than the icons generated from it.
    """
    ratio = min(box / mark.width, box / mark.height)
    return mark.resize((max(1, round(mark.width * ratio)), max(1, round(mark.height * ratio))), Image.LANCZOS)


def tile(size: int, mark: Image.Image) -> Image.Image:
    """The app icon: the mark centred on a graphite rounded square."""
    scale = 4
    big = size * scale
    canvas = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle([0, 0, big - 1, big - 1], radius=int(big * 0.22), fill=GRAPHITE)

    glyph = fit(mark, int(big * 0.78))
    canvas.alpha_composite(glyph, ((big - glyph.width) // 2, (big - glyph.height) // 2))
    return canvas.resize((size, size), Image.LANCZOS)


def plate(size: int, mark: Image.Image, colour=None) -> Image.Image:
    """The splash lockup: the mark alone on a transparent ground.

    `colour` replaces the artwork with a flat silhouette, which is how the mark
    stays legible on a light background - it is near-white by design.
    """
    scale = 4
    big = size * scale
    canvas = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    glyph = fit(mark, int(big * 0.88))

    if colour is not None:
        flat = Image.new("RGBA", glyph.size, colour)
        flat.putalpha(glyph.getchannel("A"))
        glyph = flat

    canvas.alpha_composite(glyph, ((big - glyph.width) // 2, (big - glyph.height) // 2))
    return canvas.resize((size, size), Image.LANCZOS)


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"logo source missing: {SOURCE}")
    mark = load_mark()
    print(f"mark cropped to {mark.size} from {SOURCE.name}")

    targets = {
        "static/favicon.png": tile(512, mark),
        "static/static/favicon.png": tile(512, mark),
        "static/static/favicon-96x96.png": tile(96, mark),
        "static/static/apple-touch-icon.png": tile(180, mark),
        "static/static/web-app-manifest-192x192.png": tile(192, mark),
        "static/static/web-app-manifest-512x512.png": tile(512, mark),
        "static/static/logo.png": tile(500, mark),
        "static/static/splash.png": plate(500, mark, GRAPHITE),
        "static/static/splash-dark.png": plate(500, mark),
        # The backend serves its own copy from STATIC_DIR. A production build
        # serves everything from there, so leaving it unbranded would quietly
        # revert the application to the upstream mark.
        "backend/open_webui/static/favicon.png": tile(512, mark),
        "backend/open_webui/static/favicon-96x96.png": tile(96, mark),
        "backend/open_webui/static/apple-touch-icon.png": tile(180, mark),
        "backend/open_webui/static/logo.png": tile(500, mark),
        "backend/open_webui/static/web-app-manifest-192x192.png": tile(192, mark),
        "backend/open_webui/static/web-app-manifest-512x512.png": tile(512, mark),
        "backend/open_webui/static/splash.png": plate(500, mark, GRAPHITE),
        "backend/open_webui/static/splash-dark.png": plate(500, mark),
    }
    for relative, image in targets.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
    print(f"wrote {len(targets)} raster assets")

    icon = tile(256, mark)
    for relative in ("static/static/favicon.ico", "backend/open_webui/static/favicon.ico"):
        icon.save(ROOT / relative, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("wrote 2 multi-size .ico files")

    write_vector_assets()
    write_raster_mark()


def write_vector_assets() -> None:
    """The SVG favicon and the bare marks, from the traced vector source.

    `logo-mark.svg` is the connection wheel traced from the supplied artwork,
    2 KB of path data. Being vector it can finally sit inside the SVG favicon,
    which until now could only carry an empty graphite square: embedding the
    raster mark would have bloated every page that references it.

    The bare marks exist for the UI's small logo slots. The app icon puts the
    mark at 78% inside a tile, so a 20px slot showed it at about 15px, and a
    rounded-full crop then cut the tile into a circle. A bare mark fills the
    slot instead. An <img> cannot inherit text colour, hence one per theme.
    """
    import re

    source = (HERE / "logo-mark.svg").read_text(encoding="utf-8")
    view_box = re.search(r'viewBox="([^"]+)"', source).group(1)
    path = re.search(r' d="([^"]+)"', source).group(1)
    side = float(view_box.split()[2])

    def bare(fill: str) -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}">'
            f'<path fill="{fill}" fill-rule="evenodd" d="{path}"/></svg>\n'
        )

    # Mark at 70% of the tile, matching the raster icons' visual weight.
    inset = side * 0.70
    scale = inset / side
    offset = (512 - 512 * scale) / 2
    favicon = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
        '<rect width="512" height="512" rx="113" fill="#0D1117"/>'
        f'<path fill="#FFFFFF" fill-rule="evenodd" '
        f'transform="translate({offset:.2f} {offset:.2f}) scale({512 / side * scale:.5f})" d="{path}"/>'
        '</svg>\n'
    )

    outputs = {
        "favicon.svg": favicon,
        # graphite mark for light surfaces, white for dark ones
        "logo-mark-dark.svg": bare("#0D1117"),
        "logo-mark-light.svg": bare("#FFFFFF"),
    }
    written = 0
    for name, body in outputs.items():
        for tree in ("static/static", "backend/open_webui/static"):
            (ROOT / tree / name).write_text(body, encoding="utf-8")
            written += 1
    print(f"wrote {written} .svg files")


def write_raster_mark(size: int = 512) -> None:
    """The bare mark as a PNG, drawn from the vector trace, for Word reports.

    A .docx cannot embed SVG portably, and the raster pipeline above works
    from the JPEG's luminance, whose strands come out soft - the edges that
    read as a "flower" at larger sizes. The trace is plain polygons (only M
    and Z) filled even-odd, so each ring is drawn onto its own mask and the
    masks are XOR-ed, which is exactly the even-odd rule. Drawn at 8x and
    reduced, so the edges are anti-aliased rather than stair-stepped.
    """
    import re

    source = (HERE / "logo-mark.svg").read_text(encoding="utf-8")
    side = float(re.search(r'viewBox="([^"]+)"', source).group(1).split()[2])
    path = re.search(r' d="([^"]+)"', source).group(1)

    scale = 8
    big = size * scale
    inset = big * 0.04  # a hair of margin so anti-aliasing is not clipped
    k = (big - 2 * inset) / side
    mask = Image.new("L", (big, big), 0)
    for ring in re.findall(r"M([^MZ]+)Z", path):
        numbers = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", ring)]
        points = [(inset + x * k, inset + y * k) for x, y in zip(numbers[0::2], numbers[1::2])]
        if len(points) < 3:
            continue
        layer = Image.new("L", (big, big), 0)
        ImageDraw.Draw(layer).polygon(points, fill=255)
        mask = ImageChops.logical_xor(mask.convert("1"), layer.convert("1")).convert("L")

    mask = mask.resize((size, size), Image.LANCZOS)
    mark = Image.new("RGBA", (size, size), GRAPHITE)
    mark.putalpha(mask)
    for tree in ("static/static", "backend/open_webui/static"):
        mark.save(ROOT / tree / "logo-mark.png", optimize=True)
    print("wrote 2 logo-mark.png files")


if __name__ == "__main__":
    main()
