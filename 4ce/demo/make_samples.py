"""
Generate safe, synthetic demo documents for 4CE.

    python 4ce/demo/make_samples.py

Produces a scanned-looking equipment inspection report (PNG + PDF) and a short
SOP text file, written to 4ce/demo/samples/. Everything is invented: no
proprietary or real plant data is used, which is what the problem statement
asks for.

The PNG is deliberately imperfect - slight rotation, paper tint and speckle -
so it exercises the vision and OCR path rather than clean digital text.
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent / "samples"
INK = (28, 32, 38)
PAPER = (247, 244, 236)

REPORT = [
    ("h1", "EQUIPMENT INSPECTION REPORT"),
    ("sub", "Mechanical Integrity — Routine Scheduled Inspection"),
    ("rule", ""),
    ("kv", "Report number|MIR/2026/0431"),
    ("kv", "Equipment tag|P-101B — Crude Charge Pump (standby)"),
    ("kv", "Unit|Crude Distillation Unit"),
    ("kv", "Inspection date|14 February 2026"),
    ("kv", "Inspector|R. Nair, Mechanical Inspection"),
    ("rule", ""),
    ("h2", "1. OBSERVATIONS"),
    ("p", "1.1  Casing external surface shows light surface corrosion on the"),
    ("p", "     discharge side. No measurable wall loss detected."),
    ("p", "1.2  Mechanical seal exhibits intermittent weeping, approximately"),
    ("p", "     3 to 4 drops per minute during sustained operation."),
    ("p", "1.3  Bearing housing temperature recorded at 71 degrees C against"),
    ("p", "     an alarm limit of 80 degrees C."),
    ("p", "1.4  Vibration measured at 4.1 mm/s RMS. ISO 10816 Zone B."),
    ("p", "1.5  Coupling guard fastener missing at position 3 of 4."),
    ("h2", "2. MEASUREMENTS"),
    ("kv", "Suction pressure|2.4 bar g"),
    ("kv", "Discharge pressure|18.6 bar g"),
    ("kv", "Minimum measured wall thickness|11.2 mm (nominal 12.7 mm)"),
    ("kv", "Retirement thickness|9.5 mm"),
    ("h2", "3. INSPECTOR RECOMMENDATION"),
    ("p", "Equipment remains fit for continued service. Replace the missing"),
    ("p", "coupling guard fastener before the next start. Schedule mechanical"),
    ("p", "seal replacement at the next available maintenance window."),
    ("p", "Re-inspect casing corrosion at the next turnaround."),
    ("rule", ""),
    ("p", "Prepared by: R. Nair            Reviewed by: ______________"),
]

SOP = """SOP-MEC-014  Mechanical Seal Leakage — Assessment and Action

1. Purpose
   Defines the assessment thresholds and required actions for mechanical
   seal leakage observed on centrifugal pumps in hydrocarbon service.

2. Assessment thresholds
   2.1  Below 5 drops per minute: acceptable for continued operation.
        Record the observation and monitor at the next routine round.
   2.2  Between 5 and 20 drops per minute: continued operation permitted
        only with the area supervisor's written concurrence. Seal
        replacement must be scheduled within 30 days.
   2.3  Above 20 drops per minute, or any atomised or visible spray:
        remove the equipment from service immediately.

3. Vibration limits
   3.1  ISO 10816 Zone A or B: acceptable for unrestricted operation.
   3.2  Zone C: operation permitted for a limited period. Raise a
        maintenance notification.
   3.3  Zone D: not acceptable. Remove from service.

4. Wall thickness
   4.1  Equipment is fit for service while the minimum measured wall
        thickness remains above the stated retirement thickness.
   4.2  Where remaining margin is below 2.0 mm, shorten the inspection
        interval to six months.

5. Guarding
   5.1  Rotating equipment must not be started with any coupling guard
        fastener missing. Rectify before the next start.
"""


def font(size: int, bold: bool = False):
    for path in (
        "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/couri.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def render_report() -> Image.Image:
    W, H = 1654, 2339  # A4 at 200 dpi
    canvas = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(canvas)
    x, y = 150, 150

    for kind, text in REPORT:
        if kind == "h1":
            draw.text((x, y), text, font=font(46, True), fill=INK)
            y += 70
        elif kind == "sub":
            draw.text((x, y), text, font=font(28), fill=INK)
            y += 60
        elif kind == "h2":
            y += 26
            draw.text((x, y), text, font=font(32, True), fill=INK)
            y += 52
        elif kind == "rule":
            draw.line([(x, y), (W - 150, y)], fill=INK, width=2)
            y += 28
        elif kind == "kv":
            label, value = text.split("|")
            draw.text((x, y), label, font=font(26), fill=INK)
            draw.text((x + 560, y), value, font=font(26, True), fill=INK)
            y += 42
        else:
            draw.text((x, y), text, font=font(26), fill=INK)
            y += 40

    # Make it look scanned rather than generated.
    canvas = canvas.rotate(-0.35, resample=Image.BICUBIC, fillcolor=PAPER)
    pixels = canvas.load()
    random.seed(4)
    for _ in range(int(W * H * 0.0016)):
        px, py = random.randrange(W), random.randrange(H)
        shade = random.randint(140, 205)
        pixels[px, py] = (shade, shade, shade - 8)
    return canvas.filter(ImageFilter.GaussianBlur(0.4))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report = render_report()
    report.save(OUT / "inspection_report_P-101B.png", dpi=(200, 200))
    report.convert("RGB").save(OUT / "inspection_report_P-101B.pdf", "PDF", resolution=200)
    (OUT / "SOP-MEC-014_seal_leakage.txt").write_text(SOP, encoding="utf-8")
    for path in sorted(OUT.iterdir()):
        print(f"wrote {path.relative_to(OUT.parent)} ({path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
