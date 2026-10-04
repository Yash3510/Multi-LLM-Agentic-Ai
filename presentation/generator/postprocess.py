"""Adds what pptxgenjs cannot write: a Morph transition on every slide, auto-playing entrance
animations (from anim.json) that run once each morph lands, and the deck's own colour scheme
(from theme.json, which build.cjs writes next to anim.json).

    python postprocess.py deck.raw.pptx anim.json deck.pptx

Edits are plain string insertions into each slide's XML, so namespaces and element order
stay exactly as pptxgenjs wrote them.
"""
import json
import os
import re
import sys
import zipfile

MORPH_MS = 1500

TRANSITION = (
    '<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
    'xmlns:p159="http://schemas.microsoft.com/office/powerpoint/2015/09/main">'
    '<mc:Choice Requires="p159">'
    '<p:transition spd="slow" xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" p14:dur="{ms}">'
    '<p159:morph option="byObject"/></p:transition></mc:Choice>'
    '<mc:Fallback><p:transition spd="slow"><p:fade/></p:transition></mc:Fallback>'
    "</mc:AlternateContent>"
).format(ms=MORPH_MS)

class Ids:
    def __init__(self):
        self.n = 4  # 1-4 are the root, main sequence and the two wrapper pars

    def next(self):
        self.n += 1
        return self.n


def tgt(spid):
    return f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'


def set_visible(ids, spid):
    return (
        f'<p:set><p:cBhvr><p:cTn id="{ids.next()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
        f'{tgt(spid)}<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
        '<p:to><p:strVal val="visible"/></p:to></p:set>'
    )


def anim(ids, spid, attr, frm, to, dur, extra="", bounce=False):
    b = ' p14:bounceEnd="35000"' if bounce else ""
    def val(v):
        return f'<p:fltVal val="{v}"/>' if isinstance(v, (int, float)) else f'<p:strVal val="{v}"/>'
    return (
        f'<p:anim calcmode="lin" valueType="num"{b}><p:cBhvr additive="base"><p:cTn id="{ids.next()}" dur="{dur}"{extra} fill="hold"/>'
        f'{tgt(spid)}<p:attrNameLst><p:attrName>{attr}</p:attrName></p:attrNameLst></p:cBhvr>'
        f'<p:tavLst><p:tav tm="0"><p:val>{val(frm)}</p:val></p:tav><p:tav tm="100000"><p:val>{val(to)}</p:val></p:tav></p:tavLst></p:anim>'
    )


def fade(ids, spid, dur, filt="fade"):
    return (
        f'<p:animEffect transition="in" filter="{filt}"><p:cBhvr><p:cTn id="{ids.next()}" dur="{dur}"/>'
        f"{tgt(spid)}</p:cBhvr></p:animEffect>"
    )


def effect(ids, spid, fx, delay, bounce):
    """One entrance effect as a 'With Previous' node delayed by `delay` ms."""
    preset = {"up": (42, 0), "zoom": (53, 16), "wipe": (22, 8), "fade": (10, 0), "fly": (2, 4)}[fx]
    head_id = ids.next()
    body = set_visible(ids, spid)
    if fx == "up":  # Float In
        body += fade(ids, spid, 700)
        body += anim(ids, spid, "ppt_x", "#ppt_x", "#ppt_x", 700)
        body += anim(ids, spid, "ppt_y", "#ppt_y+.1", "#ppt_y", 700, ' decel="100000"')
    elif fx == "zoom":
        body += anim(ids, spid, "ppt_w", 0, "#ppt_w", 500)
        body += anim(ids, spid, "ppt_h", 0, "#ppt_h", 500)
        body += fade(ids, spid, 500)
    elif fx == "wipe":
        body += fade(ids, spid, 500, "wipe(left)")
    elif fx == "fade":
        body += fade(ids, spid, 500)
    elif fx == "fly":  # the Circle template's bouncing fly-in from below
        body += anim(ids, spid, "ppt_x", "#ppt_x", "#ppt_x", 1200, bounce=bounce)
        body += anim(ids, spid, "ppt_y", "#ppt_y+.45", "#ppt_y", 1200, bounce=bounce)
    pb = ' p14:presetBounceEnd="35000"' if (fx == "fly" and bounce) else ""
    return (
        f'<p:par><p:cTn id="{head_id}" presetID="{preset[0]}" presetClass="entr" presetSubtype="{preset[1]}" '
        f'fill="hold" grpId="0" nodeType="withEffect"{pb}><p:stCondLst><p:cond delay="{delay}"/></p:stCondLst>'
        f"<p:childTnLst>{body}</p:childTnLst></p:cTn></p:par>"
    )


def timing(items, shapes, bounce):
    ids = Ids()
    effects, builds = [], []
    for it in items:
        spid, kind = shapes[it["name"]]
        effects.append(effect(ids, spid, it["fx"], it["at"], bounce))
        if kind == "sp":
            builds.append(f'<p:bldP spid="{spid}" grpId="0" animBg="1"/>')
        elif kind == "graphicFrame":
            builds.append(f'<p:bldGraphic spid="{spid}" grpId="0"><p:bldAsOne/></p:bldGraphic>')
    bld = f"<p:bldLst>{''.join(builds)}</p:bldLst>" if builds else ""
    return (
        '<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
        '<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
        '<p:par><p:cTn id="3" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
        '<p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst>'
        '<p:par><p:cTn id="4" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
        f"{''.join(effects)}"
        "</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>"
        "</p:childTnLst></p:cTn>"
        '<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
        '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
        "</p:seq></p:childTnLst></p:cTn></p:par></p:tnLst>"
        f"{bld}</p:timing>"
    )


SHAPE_RE = re.compile(r'<p:nv(Sp|Pic|GraphicFrame|CxnSp)Pr>\s*<p:cNvPr id="(\d+)" name="([^"]*)"')


def shape_map(xml):
    kinds = {"Sp": "sp", "Pic": "pic", "GraphicFrame": "graphicFrame", "CxnSp": "cxnSp"}
    return {m.group(3): (m.group(2), kinds[m.group(1)]) for m in SHAPE_RE.finditer(xml)}


HLINK_USE_TEXT_COLOR = (
    '<a:extLst><a:ext uri="{A12FA001-AC4F-418D-AE19-62706E023703}">'
    '<ahyp:hlinkClr xmlns:ahyp="http://schemas.microsoft.com/office/drawing/2018/hyperlinkcolor" val="tx"/>'
    "</a:ext></a:extLst>"
)


def process_slide(xml, items):
    # pptxgenjs writes the source file path as the description of a picture with no alt text
    xml = re.sub(r'descr="/[^"]*"', 'descr=""', xml)
    # PowerPoint paints links in the theme's link colour unless told to keep the run's colour,
    # which would put light-blue text on the white link buttons.
    xml = re.sub(r"<a:hlinkClick([^>]*)/>", r"<a:hlinkClick\1>" + HLINK_USE_TEXT_COLOR + "</a:hlinkClick>", xml)
    shapes = shape_map(xml)
    missing = [it["name"] for it in items if it["name"] not in shapes]
    if missing:
        raise SystemExit(f"animated shapes not found: {missing}")
    extra = TRANSITION
    if items:
        extra += (
            '<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
            'xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main">'
            f'<mc:Choice Requires="p14">{timing(items, shapes, True)}</mc:Choice>'
            f"<mc:Fallback>{timing(items, shapes, False)}</mc:Fallback></mc:AlternateContent>"
        )
    anchor = "</p:clrMapOvr>"
    assert xml.count(anchor) == 1 and "<p:timing>" not in xml and "<p:transition" not in xml
    return xml.replace(anchor, anchor + extra)


SLOTS = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"]


def apply_theme(xml, theme):
    """Replace pptxgenjs's stock Office palette and theme name with the deck's."""
    colors = theme["colors"]
    slots = "".join(f'<a:{k}><a:srgbClr val="{colors[k]}"/></a:{k}>' for k in SLOTS)
    xml, n = re.subn(r"<a:clrScheme [^>]*>.*?</a:clrScheme>", f'<a:clrScheme name="{theme["name"]}">{slots}</a:clrScheme>', xml, flags=re.S)
    assert n == 1
    return re.sub(r'(<a:theme [^>]*name=")[^"]*"', rf'\g<1>{theme["name"]}"', xml, count=1)


def main(src, anim_path, dst):
    plan = {a["slide"]: a["items"] for a in json.load(open(anim_path))}
    theme = json.load(open(os.path.join(os.path.dirname(anim_path), "theme.json")))
    zin = zipfile.ZipFile(src)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            m = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", info.filename)
            if m:
                data = process_slide(data.decode("utf-8"), plan.get(int(m.group(1)), [])).encode("utf-8")
            elif info.filename == "ppt/theme/theme1.xml":
                data = apply_theme(data.decode("utf-8"), theme).encode("utf-8")
            zout.writestr(info, data)
    print("wrote", dst)


if __name__ == "__main__":
    main(*sys.argv[1:4])
