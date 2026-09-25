"""
Generate safe, synthetic demo documents for 4CE.

    python 4ce/demo/make_samples.py

Produces a scanned-looking equipment inspection report (PNG + PDF), a short
SOP text file, a handwritten shift log and a P&ID excerpt - the last two each
with an answer key - written to 4ce/demo/samples/. Everything is invented: no
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


# ---------------------------------------------------------------------------
# A handwritten shift log and a P&ID excerpt: the other two inputs PS 26117
# names. Each comes with an answer key, so what the vision model reads can be
# checked rather than admired. Both are invented.
# ---------------------------------------------------------------------------

SHIFT_LOG = [
    "Shift log - CDU pump house - night shift 23/09",
    "02:10  P-101B seal weeping again, approx 6 drops/min.",
    "       Informed shift supervisor.",
    "03:45  P-101A running. Disch press 18.6 bar g, vib 3.9 mm/s.",
    "05:20  P-101B brg temp 74 C - rising? recheck at 06:00",
    "06:05  Coupling guard bolt missing on P-101B.",
    "       Tagged out - NOT to be started.",
    "Handed over to day shift.   K. Menon",
]
# The "6" in "approx 6 drops/min" is smudged on purpose: a reader should flag it.
SMUDGED = (1, "6")

SHIFT_LOG_KEY = """Answer key - handwritten shift log (shift_log_P-101.png)

Transcription, line by line:
""" + "\n".join(SHIFT_LOG) + """

Deliberately unclear: the seal leakage figure on the 02:10 line is smudged.
A good reading flags it as uncertain (it was written as 6) rather than
stating it with confidence.

Readings a good extraction lists:
| Time  | Equipment | Parameter            | Value | Unit       |
|-------|-----------|----------------------|-------|------------|
| 02:10 | P-101B    | Seal leakage         | 6 (?) | drops/min  |
| 03:45 | P-101A    | Discharge pressure   | 18.6  | bar g      |
| 03:45 | P-101A    | Vibration            | 3.9   | mm/s       |
| 05:20 | P-101B    | Bearing temperature  | 74    | C          |
| 06:05 | P-101B    | Coupling guard bolt  | missing | -        |
"""

PID_KEY = """Answer key - P&ID excerpt (pid_P-101_excerpt.png)

Equipment:
- T-101    Crude feed tank
- P-101A   Crude charge pump (duty)
- P-101B   Crude charge pump (standby)

Valves:
- HV-101A, HV-101B   Suction isolation valves, one per pump
- NRV-101A, NRV-101B Non-return valves on each pump discharge
- FV-101             Flow control valve on the common discharge header

Instruments:
- PT-101   Pressure transmitter on the discharge header (field-mounted)
- FE-101   Flow element: an orifice plate in the discharge header
- FT-101   Flow transmitter across FE-101 (field-mounted)
- FIC-101  Flow indicating controller in the control room: reads FT-101,
           drives FV-101

Lines:
- 8"-P-1001-A1A   T-101 to the pump suction header
- 6"-P-1002-A1A   Pump discharge header to E-101

Connections:
T-101 -> 8"-P-1001-A1A -> HV-101A -> P-101A -> NRV-101A -> discharge header
T-101 -> 8"-P-1001-A1A -> HV-101B -> P-101B -> NRV-101B -> discharge header
discharge header -> FE-101 -> FV-101 -> 6"-P-1002-A1A -> E-101 (preheat exchanger)
PT-101 taps the discharge header upstream of FE-101
FE-101 -> FT-101 -> FIC-101 -> FV-101 (dashed lines: electrical signals)
"""


def hand(size: int):
    for path in ("C:/Windows/Fonts/Inkfree.ttf", "C:/Windows/Fonts/segoepr.ttf", "C:/Windows/Fonts/LHANDW.TTF"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return font(size)


def render_shift_log() -> Image.Image:
    """Ruled paper, written in a hand that wanders: every character nudged,
    tilted and sized a little differently, as a pen would leave it."""
    W, H = 1654, 1180
    canvas = Image.new("RGB", (W, H), (250, 248, 240))
    draw = ImageDraw.Draw(canvas)
    for y in range(150, H - 40, 110):
        draw.line([(60, y), (W - 60, y)], fill=(170, 196, 222), width=2)
    draw.line([(130, 0), (130, H)], fill=(222, 150, 150), width=2)

    random.seed(11)
    pen = (22, 38, 92)
    y = 88
    for row, line in enumerate(SHIFT_LOG):
        x = 160
        for n, char in enumerate(line):
            size = random.randint(40, 46)
            glyph = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
            ImageDraw.Draw(glyph).text((size // 2, size // 3), char, font=hand(size), fill=pen + (255,))
            glyph = glyph.rotate(random.uniform(-7, 7), resample=Image.BICUBIC)
            canvas.paste(glyph, (int(x - size // 2), int(y + random.uniform(-3, 3))), glyph)
            if (row, char) == SMUDGED and line[n - 1] == " " and line[n + 1] == " ":
                # A thumb across the wet ink.
                smudge = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
                ImageDraw.Draw(smudge).ellipse((6, 6, 74, 74), fill=pen + (245,))
                smudge = smudge.filter(ImageFilter.GaussianBlur(7))
                canvas.paste(smudge, (int(x - 24), int(y - 16)), smudge)
            x += draw.textlength(char, font=hand(size)) * random.uniform(0.92, 1.04)
        y += 110 if row else 120

    canvas = canvas.rotate(0.6, resample=Image.BICUBIC, fillcolor=(250, 248, 240))
    return canvas.filter(ImageFilter.GaussianBlur(0.6))


def render_pid() -> Image.Image:
    """A small P&ID excerpt drawn with the usual symbols: a tank, isolation and
    non-return valves, two pumps, a control valve, instrument bubbles and
    labelled lines with flow arrows. Instrument bubbles follow ISA 5.1: a
    plain circle is mounted in the field, a circle with a bar across it sits
    on the control-room panel, and a dashed line is an electrical signal."""
    W, H = 2200, 1300
    canvas = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    ink, thin, small, label = (20, 20, 20), 3, font(24), font(28, True)

    def valve(cx, cy, tag, vertical=False, below=False):
        s = 22
        if vertical:
            d.polygon([(cx - s, cy - s), (cx + s, cy - s), (cx, cy)], outline=ink, width=thin)
            d.polygon([(cx - s, cy + s), (cx + s, cy + s), (cx, cy)], outline=ink, width=thin)
        else:
            d.polygon([(cx - s, cy - s), (cx - s, cy + s), (cx, cy)], outline=ink, width=thin)
            d.polygon([(cx + s, cy - s), (cx + s, cy + s), (cx, cy)], outline=ink, width=thin)
        d.text((cx - 45, cy + 30) if below else (cx - 50, cy - 70), tag, font=small, fill=ink)

    def check_valve(cx, cy, tag):
        d.rectangle((cx - 26, cy - 20, cx + 26, cy + 20), outline=ink, width=thin)
        d.line([(cx - 26, cy + 20), (cx + 26, cy - 20)], fill=ink, width=thin)
        d.text((cx - 55, cy + 28), tag, font=small, fill=ink)

    def pump(cx, cy, tag):
        d.ellipse((cx - 55, cy - 55, cx + 55, cy + 55), outline=ink, width=thin)
        d.polygon([(cx - 20, cy - 35), (cx - 20, cy + 35), (cx + 40, cy)], outline=ink, width=thin)
        d.line([(cx - 55, cy + 55), (cx - 75, cy + 85), (cx + 75, cy + 85), (cx + 55, cy + 55)], fill=ink, width=thin)
        d.text((cx - 45, cy + 95), tag, font=label, fill=ink)

    def bubble(cx, cy, tag, top="", panel=False):
        d.ellipse((cx - 50, cy - 50, cx + 50, cy + 50), outline=ink, width=thin)
        if panel:
            d.line([(cx - 50, cy), (cx + 50, cy)], fill=ink, width=2)
        d.text((cx - 22, cy - 40), top, font=small, fill=ink)
        d.text((cx - 22 if len(tag) < 4 else cx - 30, cy + 6), tag, font=small, fill=ink)

    def signal(points):
        """A dashed line from point to point, as an electrical signal is drawn."""
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            length = max(abs(x1 - x0), abs(y1 - y0))
            for s in range(0, length, 24):
                e = min(s + 12, length)
                d.line([(x0 + (x1 - x0) * s // length, y0 + (y1 - y0) * s // length),
                        (x0 + (x1 - x0) * e // length, y0 + (y1 - y0) * e // length)], fill=ink, width=2)

    def arrow(x, y):
        d.polygon([(x, y - 14), (x, y + 14), (x + 26, y)], fill=ink)

    # Tank and suction header.
    d.rectangle((80, 260, 300, 700), outline=ink, width=4)
    d.text((130, 460), "T-101", font=label, fill=ink)
    d.text((95, 720), "CRUDE FEED TANK", font=small, fill=ink)
    d.line([(300, 620), (520, 620)], fill=ink, width=4)
    arrow(420, 620)
    d.text((315, 570), '8"-P-1001-A1A', font=small, fill=ink)
    d.line([(520, 380), (520, 900)], fill=ink, width=4)

    # Two pump trains.
    for tag, y in (("A", 380), ("B", 900)):
        d.line([(520, y), (1180, y)], fill=ink, width=4)
        valve(640, y, f"HV-101{tag}")
        pump(820, y, f"P-101{tag}")
        check_valve(1020, y, f"NRV-101{tag}")
    d.text((760, 1040), "(STANDBY)", font=small, fill=ink)
    d.text((770, 520), "(DUTY)", font=small, fill=ink)

    # Common discharge header, instruments and control valve.
    d.line([(1180, 380), (1180, 900)], fill=ink, width=4)
    d.line([(1180, 640), (2080, 640)], fill=ink, width=4)
    arrow(1260, 640)
    d.line([(1330, 640), (1330, 520)], fill=ink, width=2)
    bubble(1330, 470, "101", "PT")
    # An orifice plate, the transmitter across it, and the loop to the valve.
    for x in (1492, 1508):
        d.line([(x, 605), (x, 675)], fill=ink, width=thin)
    d.text((1455, 685), "FE-101", font=small, fill=ink)
    d.line([(1484, 605), (1484, 570)], fill=ink, width=2)
    d.line([(1516, 605), (1516, 570)], fill=ink, width=2)
    bubble(1500, 520, "101", "FT")
    signal([(1500, 470), (1500, 330)])
    bubble(1500, 280, "101", "FIC", panel=True)
    signal([(1550, 280), (1760, 280), (1760, 590)])
    valve(1760, 640, "FV-101", below=True)
    d.rectangle((1735, 560, 1785, 590), outline=ink, width=thin)
    arrow(1900, 640)
    d.text((1830, 580), '6"-P-1002-A1A', font=small, fill=ink)
    d.text((1880, 670), "TO E-101", font=label, fill=ink)
    d.text((1880, 710), "(PREHEAT EXCHANGER)", font=small, fill=ink)

    # Title block.
    d.rectangle((1380, 1080, 2160, 1260), outline=ink, width=3)
    d.text((1400, 1095), "P&ID EXCERPT - CRUDE CHARGE PUMPS P-101A/B", font=label, fill=ink)
    d.text((1400, 1145), "Unit: Crude Distillation   Sheet 3 of 12   Rev C", font=small, fill=ink)
    d.text((1400, 1195), "SYNTHETIC - FOR DEMONSTRATION ONLY", font=small, fill=ink)
    return canvas


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report = render_report()
    report.save(OUT / "inspection_report_P-101B.png", dpi=(200, 200))
    report.convert("RGB").save(OUT / "inspection_report_P-101B.pdf", "PDF", resolution=200)
    (OUT / "SOP-MEC-014_seal_leakage.txt").write_text(SOP, encoding="utf-8")
    render_shift_log().save(OUT / "shift_log_P-101.png", dpi=(150, 150))
    (OUT / "shift_log_P-101_answer_key.txt").write_text(SHIFT_LOG_KEY, encoding="utf-8")
    render_pid().save(OUT / "pid_P-101_excerpt.png", dpi=(200, 200))
    (OUT / "pid_P-101_excerpt_answer_key.txt").write_text(PID_KEY, encoding="utf-8")
    for path in sorted(OUT.iterdir()):
        print(f"wrote {path.relative_to(OUT.parent)} ({path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
