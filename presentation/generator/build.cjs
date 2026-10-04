// Builds the Team Kern SIH 2026 deck in the 4CE chat UI's design system: the app's greys and
// violet, Apple's SF Pro with New York italics for emphasis, and the chat UI's own components
// (input box, agent stepper, status chips, approval bar, file cards, checklist).
//
// Every slide carries the same named "actors" - !!glow, !!canvas, !!px1-7, !!mark, !!eyebrow,
// !!title - in new positions, so PowerPoint's Morph transition moves them between slides: the
// light canvas sweeps across between dark and light scenes, the pixel blocks drift and the 4CE
// mark turns. postprocess.py adds the Morph transitions and the entrance animations in anim.json.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const OUT = process.argv[2] || path.join(__dirname, "deck.raw.pptx");
const A = (f) => path.join(__dirname, "assets", f);
const LOGO = JSON.parse(fs.readFileSync(A("logo.json"), "utf8"));
const W = 13.333, H = 7.5;

// The 4CE chat UI palette: page #171717, cards #262626, borders #333, muted #9B9B9B,
// light canvas #EEEFF1 with #666 muted text, violet-600/400, emerald-400 for "passed",
// amber-400 for "checked".
const THEME = {
	name: "4CE",
	headFontFace: "SF Pro Display",
	bodyFontFace: "SF Pro Text",
	colors: {
		dk1: "171717", lt1: "EEEFF1", dk2: "262626", lt2: "FFFFFF",
		accent1: "7C3AED", accent2: "A78BFA", accent3: "34D399", accent4: "FBBF24",
		accent5: "9B9B9B", accent6: "666666", hlink: "A78BFA", folHlink: "7C3AED",
	},
};
const HEAD = "+mj-lt";
const SERIF = "New York"; // Apple's serif, for the demo's italic emphasis words
const MONO = "SF Mono";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "4CE - Sovereign On-Premise Agentic AI Workbench";
pres.author = "Team Kern";
pres.subject = "Smart India Hackathon 2026 - SIH26117";
const C = pres.SchemeColor;

// Colour roles for the two scenes. A dark card on a light slide is drawn with DARK.
const DARK = {
	name: "dark", text: C.background1, muted: { color: C.accent5 }, card: C.text2, border: { color: C.background1, transparency: 85, width: 0.75 },
	accent: C.accent2, button: C.background1, buttonText: C.text1, tone: "light", accentTone: "lilac",
};
const LIGHT = {
	name: "light", text: C.text1, muted: { color: C.accent6 }, card: C.background2, border: { color: C.text1, transparency: 86, width: 0.75 },
	accent: C.accent1, button: C.text1, buttonText: C.background1, tone: "dark", accentTone: "violet",
};

pres.defineSlideMaster({ title: "4CE", background: { color: THEME.colors.dk1 } });

// ---------------------------------------------------------------- morph actors
const PX = [[0.14, 0.28], [0.28, 0.14], [0.14, 0.14], [0.14, 0.28], [0.28, 0.14], [0.14, 0.14], [0.14, 0.14]];
const PATTERN = [[-1.05, -0.45], [-0.55, 0.2], [0.05, -0.6], [0.6, 0.05], [1.0, -0.4], [-0.2, 0.6], [0.95, 0.55]];
// The pixel blocks orbit a point beside the title, turning 50 degrees a slide.
function constellation(i, fx = 10.45, fy = 0.95) {
	const a = (i * 50 * Math.PI) / 180;
	return PATTERN.map(([dx, dy]) => [fx + dx * Math.cos(a) - dy * Math.sin(a), fy + 0.55 * (dx * Math.sin(a) + dy * Math.cos(a))]);
}
const RIGHT = [13.533, 0, 0.2, H], LEFT = [-0.4, 0, 0.2, H], FULL = [0, 0, W, H];
const MARK_CORNER = (i) => [12.25, 0.6, 0.48, (i * 60) % 360];
const STATES = [
	/* 1 */ { mode: "dark", canvas: RIGHT, glow: [-3.2, 3.4], mark: [4.62, 1.45, 1.25, 0],
		px: [[3.75, 1.3], [3.2, 2.0], [4.05, 2.65], [9.25, 1.2], [9.75, 1.9], [9.15, 2.5], [10.45, 1.45]] },
	/* 2 */ { mode: "light", canvas: FULL, glow: [-3.2, 3.4] },
	/* 3 */ { mode: "dark", canvas: LEFT, glow: [9.0, 3.8] },
	/* 4 */ { mode: "light", canvas: FULL, glow: [9.0, 3.8] },
	/* 5 */ { mode: "dark", canvas: RIGHT, glow: [-3.4, 3.6] },
	/* 6 */ { mode: "light", canvas: FULL, glow: [-3.4, 3.6] },
	/* 7 */ { mode: "dark", canvas: LEFT, glow: [9.2, 3.6] },
	/* 8 */ { mode: "light", canvas: FULL, glow: [9.2, 3.6] },
	/* 9 */ { mode: "dark", canvas: RIGHT, glow: [-3.0, 3.8] },
	/* 10 */ { mode: "light", canvas: FULL, glow: [-3.0, 3.8], mark: [5.27, 0.78, 0.9, 0],
		px: [[3.9, 0.7], [3.3, 1.25], [4.35, 1.6], [9.15, 0.7], [9.75, 1.15], [8.95, 1.5], [10.3, 1.6]] },
];

const ANIM = [];
let cur = null;

function logoPoints(size) {
	return LOGO.flatMap((ring) => [
		...ring.map(([x, y], k) => ({ x: x * size, y: y * size, ...(k === 0 ? { moveTo: true } : {}) })),
		{ close: true },
	]);
}
function mark(slide, x, y, size, rot, fill, name) {
	slide.addShape(pres.ShapeType.custGeom, { x, y, w: size, h: size, rotate: rot, points: logoPoints(size), fill: { color: fill }, objectName: name });
}

function startSlide(section, notes, eyebrow) {
	if (section) pres.addSection({ title: section });
	const slide = pres.addSlide({ masterName: "4CE", sectionTitle: section || cur.section });
	const idx = cur ? cur.idx + 1 : 1;
	const st = STATES[idx - 1];
	cur = { slide, idx, n: 0, anims: [], section: section || cur.section, m: st.mode === "dark" ? DARK : LIGHT };
	ANIM.push({ slide: idx, items: cur.anims });

	slide.addImage({ path: A("glow.png"), x: st.glow[0], y: st.glow[1], w: 7.5, h: 7.5, objectName: "!!glow", altText: "" });
	const [cx, cy, cw, ch] = st.canvas;
	slide.addShape(pres.ShapeType.rect, { objectName: "!!canvas", x: cx, y: cy, w: cw, h: ch, fill: { color: C.background1 } });
	const px = st.px || constellation(idx);
	px.forEach(([x, y], k) => slide.addShape(pres.ShapeType.rect, { objectName: `!!px${k + 1}`, x, y, w: PX[k][0], h: PX[k][1], fill: { color: C.accent1 } }));
	const [mx, my, ms, mr] = st.mark || MARK_CORNER(idx);
	mark(slide, mx, my, ms, mr, cur.m.text, "!!mark");
	if (eyebrow) text(eyebrow, { objectName: "!!eyebrow", x: 0.6, y: 0.42, w: 8, h: 0.3, fontSize: 11, bold: true, charSpacing: 2, ...cur.m.muted });
	if (notes) slide.addNotes(notes);
	return slide;
}

// ---------------------------------------------------------------- primitives
function nm(fx, at) {
	const name = `s${cur.idx}_${++cur.n}`;
	if (fx) cur.anims.push({ name, fx, at });
	return name;
}
function text(t, o, fx, at) {
	cur.slide.addText(t, { isTextBox: true, margin: 0, valign: "top", ...o, objectName: o.objectName || nm(fx, at) });
}
function shape(type, o, fx, at) {
	cur.slide.addShape(type, { ...o, objectName: nm(fx, at) });
}
function icon(name, tone, x, y, s, fx, at) {
	cur.slide.addImage({ path: A(`icon-${name}-${tone}.png`), x, y, w: s, h: s, objectName: nm(fx, at), altText: "" });
}
// Title in the demo's voice: a plain clause, then an italic New York clause in violet.
function title(plain, accent, o = {}) {
	const m = cur.m;
	text([
		{ text: plain, options: { fontFace: HEAD, color: m.text, charSpacing: -0.5 } },
		{ text: accent, options: { fontFace: SERIF, italic: true, color: m.accent } },
	], { objectName: "!!title", x: 0.6, y: 0.75, w: 9.2, h: 0.85, fontSize: 36, valign: "middle", ...o });
}
const label = (m, t, x, y, w, fx, at) =>
	text(t, { x, y, w, h: 0.28, fontSize: 10, bold: true, charSpacing: 2, ...m.muted }, fx, at);

// ---------------------------------------------------------------- chat UI components
const shadow = () => ({ type: "outer", color: "000000", opacity: 0.18, blur: 24, offset: 8, angle: 90 });
function card(m, x, y, w, h, fx, at, o = {}) {
	shape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.16, fill: { color: m.card }, line: m.border, ...o }, fx, at);
}
// A dark panel on the light canvas, like the chat window in the demo's light scenes.
function island(x, y, w, h, fx, at) {
	shape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.16, fill: { color: C.text1 }, shadow: shadow() }, fx, at);
}
const chipWidth = (t, mono) => t.length * (mono ? 0.092 : 0.078) + 0.28;
// Status pill. kind: plain (outlined), fill (filled card grey), green / amber (status), violet.
function chip(m, x, y, t, kind = "plain", fx = "zoom", at = 0, mono = false) {
	const w = chipWidth(t, mono);
	const look = {
		plain: { line: m.border, color: m.text },
		fill: { fill: { color: C.text2 }, color: C.background1 },
		green: { line: { color: C.accent3, width: 1 }, color: C.accent3 },
		amber: { line: { color: C.accent4, width: 1 }, color: C.accent4 },
		violet: { fill: { color: C.accent1 }, color: C.background1 },
	}[kind];
	shape(pres.ShapeType.roundRect, { x, y, w, h: 0.32, rectRadius: 0.16, ...(look.fill ? { fill: look.fill } : {}), ...(look.line ? { line: look.line } : {}) }, fx, at);
	text(t, { x, y, w, h: 0.32, fontSize: 11, color: look.color, align: "center", valign: "middle", ...(mono ? { fontFace: MONO } : {}) }, fx, at);
	return w;
}
// Chips laid out left to right, wrapping at maxW. Returns the number of rows.
function chips(m, x, y, maxW, items, kind, at, step = 60) {
	let cx = x, cy = y, rows = 1;
	items.forEach((t, i) => {
		const w = chipWidth(t);
		if (cx + w > x + maxW && cx > x) { cx = x; cy += 0.42; rows++; }
		chip(m, cx, cy, t, kind, "zoom", at + i * step);
		cx += w + 0.1;
	});
	return rows;
}
// Inverse pill button, optionally linked.
function button(m, x, y, t, url, fx, at, w = chipWidth(t) + 0.15) {
	shape(pres.ShapeType.roundRect, { x, y, w, h: 0.36, rectRadius: 0.18, fill: { color: m.button } }, fx, at);
	text([{ text: t, options: url ? { hyperlink: { url }, color: m.buttonText } : {} }],
		{ x, y, w, h: 0.36, fontSize: 11.5, bold: true, color: m.buttonText, align: "center", valign: "middle" }, fx, at);
	return w;
}
function checkbox(x, y, s, fx, at) {
	shape(pres.ShapeType.roundRect, { x, y, w: s, h: s, rectRadius: s * 0.22, fill: { color: C.accent1 } }, fx, at);
	icon("check", "light", x + s * 0.18, y + s * 0.18, s * 0.64, fx, at);
}
function iconTile(x, y, s, name, fill, tone, fx, at) {
	shape(pres.ShapeType.roundRect, { x, y, w: s, h: s, rectRadius: s * 0.24, fill: { color: fill } }, fx, at);
	icon(name, tone, x + s * 0.24, y + s * 0.24, s * 0.52, fx, at);
}
// The agent pipeline stepper (TONY > FRIDAY > JARVIS > ULTRON > YOU).
function stepper(m, x, y, w, steps, o = {}) {
	const gap = w / (steps.length - 1 || 1), d = 0.16, at = o.at || 0;
	steps.forEach((s, i) => {
		const sx = x + i * gap;
		if (i < steps.length - 1) {
			shape(pres.ShapeType.line, { x: sx + d, y: y + d / 2, w: gap - d, h: 0, line: { color: o.dashed ? C.accent2 : C.accent5, width: 1, ...(o.dashed ? { dashType: "dash" } : {}) } }, "wipe", at + i * 160 + 80);
		}
		const hi = o.highlight === i;
		shape(pres.ShapeType.ellipse, { x: sx, y, w: d, h: d, ...(hi ? { fill: { color: C.accent1 } } : {}), line: { color: hi ? C.accent1 : m.text, width: 1.25 } }, "zoom", at + i * 160);
		if (s.label) text(s.label, { x: sx, y: y + 0.26, w: s.w || 1, h: 0.24, fontSize: 9.5, bold: true, charSpacing: 1, color: hi ? m.accent : m.text }, "up", at + i * 160);
	});
}
function fileCard(m, x, y, w, h, iconName, head, meta, btn, url, at) {
	card(m, x, y, w, h, "up", at);
	iconTile(x + 0.22, y + (h - 0.56) / 2, 0.56, iconName, m === DARK ? C.text1 : C.background1, m.tone, "up", at);
	const tw = w - 0.95 - (btn ? chipWidth(btn) + 0.6 : 0.25);
	text(head, { x: x + 0.95, y: y + h / 2 - 0.3, w: tw, h: 0.3, fontSize: 13, bold: true, color: m.text, valign: "middle" }, "up", at);
	text(meta, { x: x + 0.95, y: y + h / 2, w: tw, h: 0.28, fontSize: 10.5, ...m.muted }, "up", at);
	if (btn) button(m, x + w - chipWidth(btn) - 0.4, y + (h - 0.36) / 2, btn, url, "zoom", at + 150);
}

// ================================================================= 1. TITLE (dark)
startSlide("Opening",
	"Smart India Hackathon 2026, problem statement SIH26117: a sovereign, on-premise agentic AI workbench that runs " +
	"open-weight multimodal LLMs on confidential industrial data. Theme Smart Automation, category Software. We are Team Kern, and this is 4CE.");
text("4CE", { x: 6.12, y: 1.35, w: 3.4, h: 1.45, fontFace: HEAD, bold: true, fontSize: 100, charSpacing: -2, color: C.accent2, valign: "middle" }, "fade", 0);
title("Sovereign ", "AI Workbench", { x: 0.6, y: 2.95, w: 12.13, h: 0.7, fontSize: 30, align: "center" });
text("Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work",
	{ x: 2.67, y: 3.7, w: 8.0, h: 0.62, fontSize: 15, align: "center", ...DARK.muted }, "up", 150);
// the chat input box carries the hackathon details
{
	const x = 2.67, y = 4.65, w = 8.0, at = 400;
	card(DARK, x, y, w, 1.32, "up", at);
	text("Smart India Hackathon 2026  ·  Problem statement SIH26117", { x: x + 0.3, y: y + 0.2, w: w - 0.6, h: 0.4, fontSize: 15, color: C.background1, valign: "middle" }, "up", at);
	icon("plus", "muted", x + 0.3, y + 0.86, 0.22, "up", at);
	icon("sliders", "muted", x + 0.66, y + 0.86, 0.22, "up", at);
	let cx = x + 1.05;
	cx += chip(DARK, cx, y + 0.81, "Theme · Smart Automation", "plain", "zoom", at + 300) + 0.1;
	chip(DARK, cx, y + 0.81, "Category · Software", "plain", "zoom", at + 380);
	text("Team Kern  ·  4CE (ACE)", { x: x + 4.95, y: y + 0.81, w: 2.0, h: 0.32, fontSize: 11, align: "right", valign: "middle", ...DARK.muted }, "up", at);
	icon("chevron", "muted", x + 7.0, y + 0.86, 0.2, "up", at);
	shape(pres.ShapeType.ellipse, { x: x + 7.32, y: y + 0.78, w: 0.38, h: 0.38, fill: { color: C.background1 } }, "zoom", at + 500);
	icon("arrowUp", "dark", x + 7.41, y + 0.87, 0.2, "zoom", at + 500);
}

// ================================================================= 2. OUR SOLUTION (light)
startSlide("Solution",
	"Our solution rests on four pillars. Sovereignty: local LLMs, so data stays inside. Ingestion: legacy files become usable intelligence. " +
	"Governance: tool execution waits for human approval. Trust: every generated answer is source-verified. " +
	"On the right is how that looks in the 4CE chat: a local model, grounded sources, ULTRON's check, a human release and zero external calls.",
	"OUR SOLUTION");
title("Four pillars, ", "one workbench.");
[
	["Sovereignty", "Local LLMs  →  data stays inside"],
	["Ingestion", "Legacy files  →  usable intelligence"],
	["Governance", "Tool execution  →  human approval"],
	["Trust", "Generated answer  →  source-verified"],
].forEach(([h, d], i) => {
	const y = 2.05 + i * 1.15, at = i * 220;
	checkbox(0.6, y + 0.06, 0.34, "zoom", at + 120);
	text(h, { x: 1.15, y: y - 0.04, w: 5.6, h: 0.5, fontFace: HEAD, fontSize: 24, color: C.text1, valign: "middle" }, "up", at);
	text(d, { x: 1.15, y: y + 0.46, w: 5.6, h: 0.36, fontSize: 15, ...LIGHT.muted }, "up", at);
});
{
	const x = 7.3, y = 1.95, at = 900;
	island(x, y, 5.43, 4.9, "up", at);
	shape(pres.ShapeType.roundRect, { x: 8.75, y: y + 0.3, w: 3.68, h: 0.74, rectRadius: 0.18, fill: { color: C.text2 } }, "up", at + 150);
	text("Draft an approval note: is pump P-101B fit to restart?", { x: 8.95, y: y + 0.3, w: 3.3, h: 0.74, fontSize: 12, color: C.background1, valign: "middle" }, "up", at + 150);
	cur.slide.addShape(pres.ShapeType.custGeom, { x: x + 0.3, y: y + 1.32, w: 0.28, h: 0.28, points: logoPoints(0.28), fill: { color: C.background1 }, objectName: nm("up", at + 300) });
	text("4CE / TONY (Orchestrator)", { x: x + 0.7, y: y + 1.3, w: 3.5, h: 0.32, fontSize: 12, color: C.background1, valign: "middle" }, "up", at + 300);
	let cx = x + 0.3;
	cx += chip(DARK, cx, y + 1.85, "Local qwen3-vl-4b", "plain", "zoom", at + 450) + 0.1;
	chip(DARK, cx, y + 1.85, "Grounded 2 sources", "plain", "zoom", at + 520);
	chip(DARK, x + 0.3, y + 2.27, "Checked · ULTRON passed it", "amber", "zoom", at + 600);
	chip(DARK, x + 0.3, y + 2.69, "Released by 4CE Administrator", "green", "zoom", at + 680);
	cx = x + 0.3;
	cx += chip(DARK, cx, y + 3.11, "0 external calls, observed", "green", "zoom", at + 760) + 0.1;
	chip(DARK, cx, y + 3.11, "Audit", "plain", "zoom", at + 830);
	// file card, drawn in the dark scene's colours
	shape(pres.ShapeType.roundRect, { x: x + 0.3, y: y + 3.68, w: 4.83, h: 0.9, rectRadius: 0.14, fill: { color: C.text2 } }, "up", at + 950);
	iconTile(x + 0.48, y + 3.85, 0.56, "fileText", C.text1, "light", "up", at + 950);
	text("Approval note", { x: x + 1.2, y: y + 3.83, w: 2.3, h: 0.3, fontSize: 12.5, bold: true, color: C.background1, valign: "middle" }, "up", at + 950);
	text("Word report · stored on this machine", { x: x + 1.2, y: y + 4.12, w: 2.6, h: 0.28, fontSize: 10, ...DARK.muted }, "up", at + 950);
	button(DARK, x + 3.88, y + 3.95, "Download", null, "zoom", at + 1100, 1.05);
}

// ================================================================= 3. WHY DIFFERENT (dark)
startSlide(null,
	"Why it is different. Generated code never runs on the host: it goes to a sandbox with no network, a read-only filesystem and no capabilities. " +
	"Every action passes a central control layer, and sensitive ones stop at YOU - a human approves before anything is released. " +
	"And the architecture is model-independent: Qwen, Gemma, Mistral or another open model. Change the model, not the architecture.",
	"WHY DIFFERENT");
title("Safe by ", "design.");
const COLS = [0.6, 4.81, 9.02], CW = 3.71;
[
	["box", "Isolated sandbox execution", "AI-generated code  →  isolated environment  →  controlled execution."],
	["sliders", "Centralised AI control", "Every action  →  control layer  →  authorization  →  execution."],
	["cpu", "Model-independent architecture", "Runs Qwen, Gemma, Mistral or other open-source models."],
].forEach(([ic, h, d], i) => {
	const x = COLS[i], y = 1.95, at = i * 250;
	card(DARK, x, y, CW, 4.9, "up", at);
	icon(ic, "lilac", x + 0.3, y + 0.3, 0.36, "up", at);
	text(h, { x: x + 0.3, y: y + 0.8, w: CW - 0.6, h: 0.6, fontSize: 16, bold: true, color: C.background1 }, "up", at);
	text(d, { x: x + 0.3, y: y + 1.42, w: CW - 0.6, h: 0.7, fontSize: 12.5, ...DARK.muted }, "up", at);
});
{ // sandbox flags, from the demo's "Sandboxed execution result"
	const x = COLS[0] + 0.3, y = 1.95, at = 800;
	label(DARK, "SANDBOXED EXECUTION", x, y + 2.2, 3, "up", at);
	["--network none", "--read-only", "--cap-drop ALL"].forEach((f, k) => chip(DARK, x, y + 2.58 + k * 0.42, f, "fill", "zoom", at + 100 + k * 90, true));
	chip(DARK, x, y + 3.95, "Exit code: 0", "green", "zoom", at + 450, true);
}
{ // the agent pipeline, ending at the human
	const x = COLS[1] + 0.3, y = 1.95, at = 1100;
	label(DARK, "EVERY ACTION, IN ORDER", x, y + 2.2, 3, "up", at);
	stepper(DARK, x, y + 2.62, 2.75, [{ label: "TONY", w: 0.7 }, { label: "FRIDAY", w: 0.7 }, { label: "JARVIS", w: 0.7 }, { label: "ULTRON", w: 0.7 }, { label: "YOU", w: 0.7 }], { highlight: 4, at });
	shape(pres.ShapeType.roundRect, { x, y: y + 3.4, w: 1.45, h: 0.36, rectRadius: 0.18, line: { color: C.accent1, width: 1 } }, "up", at + 900);
	text("Type approve", { x: x + 0.15, y: y + 3.4, w: 1.2, h: 0.36, fontSize: 10.5, valign: "middle", ...DARK.muted }, "up", at + 900);
	text("Withhold", { x: x + 1.55, y: y + 3.4, w: 0.7, h: 0.36, fontSize: 10.5, color: C.background1, valign: "middle" }, "up", at + 900);
	button(DARK, x + 2.3, y + 3.4, "Approve", null, "zoom", at + 1000, 0.81);
	text("Sensitive actions  →  mandatory human approval", { x, y: y + 3.95, w: 3.1, h: 0.5, fontSize: 11.5, color: C.accent2 }, "up", at + 1100);
}
{ // model picker
	const x = COLS[2] + 0.3, y = 1.95, at = 1500;
	shape(pres.ShapeType.roundRect, { x, y: y + 2.15, w: 3.11, h: 0.38, rectRadius: 0.19, line: DARK.border }, "up", at);
	text("4CE / TONY (Orchestrator)", { x: x + 0.18, y: y + 2.15, w: 2.5, h: 0.38, fontSize: 11, color: C.background1, valign: "middle" }, "up", at);
	icon("chevron", "muted", x + 2.8, y + 2.24, 0.2, "up", at);
	shape(pres.ShapeType.roundRect, { x, y: y + 2.63, w: 3.11, h: 1.45, rectRadius: 0.12, fill: { color: C.text1 }, line: DARK.border }, "up", at + 150);
	["Qwen", "Gemma", "Mistral", "Other open-source models"].forEach((mdl, k) => {
		text(mdl, { x: x + 0.2, y: y + 2.72 + k * 0.32, w: 2.4, h: 0.3, fontSize: 11.5, color: k === 0 ? C.background1 : C.accent5, valign: "middle" }, "up", at + 200 + k * 80);
		if (k === 0) icon("check", "lilac", x + 2.75, y + 2.78, 0.2, "zoom", at + 300);
	});
	text("Change the model, not the architecture.", { x, y: y + 4.18, w: 3.11, h: 0.55, fontFace: SERIF, italic: true, fontSize: 13, color: C.accent2 }, "up", at + 600);
}

// ================================================================= 4. TECHNICAL APPROACH (light)
startSlide("Technical",
	"Technical approach. Python and Bash at the core; FastAPI, Uvicorn, Socket.io and SvelteKit with JWT session auth for the platform; " +
	"Bionic with Qwen and Gemma models and nomic-embed-text v1.5 embeddings for AI; SQLite and ChromaDB for storage; Docker with hardening " +
	"flags for isolated execution; python-docx for document generation; and a custom test harness. Over 75 percent of the prototype is built, and it is all on GitHub.",
	"TECHNICAL APPROACH");
title("Built on an open, ", "local stack.");
{
	const x = 0.6, y = 1.95, at = 0;
	island(x, y, 8.3, 4.9, "up", at);
	text("Tech stack", { x: x + 0.3, y: y + 0.25, w: 3, h: 0.32, fontSize: 13, bold: true, color: C.background1, valign: "middle" }, "up", at);
	[
		["Language & runtime", ["Python", "Bash"]],
		["Application platform", ["FastAPI", "Uvicorn", "Socket.io", "SvelteKit", "JWT session auth"]],
		["AI / ML", ["Bionic", "Qwen models", "Gemma models", "nomic-embed-text-v1.5"]],
		["Data & storage", ["SQLite", "ChromaDB"]],
		["Execution & isolation", ["Docker", "Hardening flags"]],
		["Document generation", ["python-docx"]],
		["Deployment & tooling", ["Custom test harness"]],
	].forEach(([h, items], i) => {
		const ry = y + 0.78 + i * 0.58, rat = at + 150 + i * 110;
		text(h, { x: x + 0.3, y: ry, w: 1.9, h: 0.32, fontSize: 12, bold: true, color: C.background1, valign: "middle" }, "up", rat);
		chips(DARK, x + 2.25, ry, 5.75, items, "fill", rat, 40);
	});
}
{
	const x = 9.15, w = 3.58, at = 600;
	card(LIGHT, x, 1.95, w, 2.75, "up", at);
	label(LIGHT, "PROTOTYPE", x + 0.3, 2.22, 2, "up", at);
	text("75%+", { x: x + 0.3, y: 2.5, w: w - 0.6, h: 1.05, fontFace: HEAD, fontSize: 64, charSpacing: -2, color: C.text1, valign: "middle" }, "up", at);
	text("of the prototype is already built", { x: x + 0.3, y: 3.6, w: w - 0.6, h: 0.32, fontSize: 13, ...LIGHT.muted }, "up", at);
	shape(pres.ShapeType.roundRect, { x: x + 0.3, y: 4.2, w: w - 0.6, h: 0.12, rectRadius: 0.06, fill: { color: C.text1, transparency: 88 } }, "up", at);
	shape(pres.ShapeType.roundRect, { x: x + 0.3, y: 4.2, w: (w - 0.6) * 0.75, h: 0.12, rectRadius: 0.06, fill: { color: C.accent1 } }, "wipe", at + 500);
	card(LIGHT, x, 4.95, w, 1.9, "up", at + 300);
	iconTile(x + 0.3, 5.23, 0.56, "github", C.text1, "light", "up", at + 300);
	text("Multi-LLM-Agentic-Ai", { x: x + 1.02, y: 5.2, w: 2.5, h: 0.32, fontSize: 13, bold: true, color: C.text1, valign: "middle" }, "up", at + 300);
	text("GitHub repository · Yash3510", { x: x + 1.02, y: 5.5, w: 2.5, h: 0.28, fontSize: 10.5, ...LIGHT.muted }, "up", at + 300);
	button(LIGHT, x + 0.3, 6.15, "Open the repository", "https://github.com/Yash3510/Multi-LLM-Agentic-Ai", "zoom", at + 450, w - 0.6);
}

// ================================================================= 5. FEASIBILITY - RISK (dark)
startSlide("Feasibility",
	"Feasibility: each real risk we hit has a mitigation in place. Cloud dependency - a local-only stack with outbound paths disabled. " +
	"A 65K context overflowed 6 GB of VRAM and fell back to CPU with 20-plus-minute inference; an 8K context fits VRAM and restores GPU inference. " +
	"Hallucinated findings are caught by ULTRON verification with bounded replanning. Generated code runs only in a hardened Docker sandbox.",
	"FEASIBILITY  ·  RISK ASSESSMENT & MITIGATION");
title("Every risk, ", "answered.");
{
	const x = 0.6, y = 1.95, w = 12.13, at = 0;
	card(DARK, x, y, w, 4.9, "up", at);
	label(DARK, "RISK", x + 0.35, y + 0.3, 2, "up", at);
	label(DARK, "MITIGATION", x + 6.6, y + 0.3, 2, "up", at);
	[
		["Cloud dependency", "Data could leave the enterprise", "Local-only stack + outbound paths disabled"],
		["65K context window", "KV cache exceeded 6 GB VRAM → CPU fallback → 20+ min inference", "8K context fits VRAM → GPU inference restored"],
		["AI hallucination", "Generated findings could be incorrect", "ULTRON verification + bounded replan"],
		["Generated-code risk", "AI code could reach the host or network", "Hardened Docker sandbox → isolated execution"],
	].forEach(([r, rd, mtg], i) => {
		const ry = y + 0.72 + i * 1.02, rat = at + 200 + i * 280;
		shape(pres.ShapeType.line, { x: x + 0.35, y: ry, w: w - 0.7, h: 0, line: { ...DARK.border } }, "wipe", rat);
		shape(pres.ShapeType.ellipse, { x: x + 0.35, y: ry + 0.29, w: 0.11, h: 0.11, fill: { color: C.accent4 } }, "zoom", rat);
		text(r, { x: x + 0.62, y: ry + 0.16, w: 5.4, h: 0.36, fontSize: 15, bold: true, color: C.background1, valign: "middle" }, "up", rat);
		text(rd, { x: x + 0.62, y: ry + 0.52, w: 5.4, h: 0.42, fontSize: 12, ...DARK.muted }, "up", rat);
		text("→", { x: x + 6.0, y: ry + 0.16, w: 0.4, h: 0.7, fontSize: 18, color: C.accent2, valign: "middle" }, "wipe", rat + 100);
		text(mtg, { x: x + 6.6, y: ry + 0.16, w: 4.55, h: 0.7, fontSize: 14, color: C.background1, valign: "middle" }, "up", rat + 150);
		shape(pres.ShapeType.ellipse, { x: x + w - 0.83, y: ry + 0.35, w: 0.32, h: 0.32, line: { color: C.accent3, width: 1 } }, "zoom", rat + 250);
		icon("check", "green", x + w - 0.77, ry + 0.41, 0.2, "zoom", rat + 250);
	});
}

// ================================================================= 6. VIABILITY - RESOURCES & ECONOMICS (light)
startSlide(null,
	"What it takes to run: local compute with a GPU recommended, Docker and a local model server, persistent storage next to the enterprise data, " +
	"and proven frameworks. How it pays: potentially lower recurring AI costs for sustained, high-volume workloads; monetisation through enterprise " +
	"licensing plus setup and integration; and recurring revenue from support, maintenance and custom agents.",
	"VIABILITY  ·  RESOURCES & ECONOMICS");
title("What it takes, ", "what it pays.");
{
	const x = 0.6, y = 1.95, w = 12.13, at = 0;
	island(x, y, w, 2.3, "up", at);
	label(DARK, "RESOURCE REQUIREMENTS", x + 0.3, y + 0.25, 4, "up", at);
	const tw = (w - 0.6 - 0.45) / 4;
	[
		["Local compute + GPU (recommended)", "cpu"],
		["Docker + local model server", "docker"],
		["Persistent storage + enterprise data", "hardDrive"],
		["Proven frameworks", "layers"],
	].forEach(([t, ic], i) => {
		const tx = x + 0.3 + i * (tw + 0.15), tat = at + 150 + i * 130;
		shape(pres.ShapeType.roundRect, { x: tx, y: y + 0.65, w: tw, h: 1.35, rectRadius: 0.12, fill: { color: C.text2 } }, "up", tat);
		icon(ic, "lilac", tx + 0.22, y + 0.85, 0.32, "up", tat);
		text(t, { x: tx + 0.22, y: y + 1.27, w: tw - 0.4, h: 0.6, fontSize: 13, bold: true, color: C.background1 }, "up", tat);
	});
}
label(LIGHT, "ECONOMIC APPROACH", 0.6, 4.55, 4, "up", 700);
[
	["Lower recurring AI costs", "Potentially lower costs for sustained, high-volume workloads", "trendDown"],
	["Enterprise licensing", "Monetised through licensing plus setup and integration", "briefcase"],
	["Recurring revenue", "Support, maintenance and custom agents", "repeat"],
].forEach(([h, d, ic], i) => {
	const x = 0.6 + i * 4.127, at = 800 + i * 160;
	card(LIGHT, x, 4.95, 3.877, 1.9, "up", at);
	iconTile(x + 0.3, 5.25, 0.5, ic, C.accent1, "light", "up", at);
	text(h, { x: x + 0.95, y: 5.25, w: 2.8, h: 0.5, fontSize: 15, bold: true, color: C.text1, valign: "middle" }, "up", at);
	text(d, { x: x + 0.3, y: 5.95, w: 3.3, h: 0.7, fontSize: 12.5, ...LIGHT.muted }, "up", at);
});

// ================================================================= 7. IMPACT (dark)
startSlide("Impact",
	"Impact and benefits. Conversational: safer AI interactions with human oversight. Research: private AI research and controlled experimentation. " +
	"National: AI and data sovereignty with less external dependence. Technical: local LLM plus RAG, multi-agent orchestration, sandboxing, verification " +
	"and auditability. Economic and industrial: lower recurring AI costs and secure adoption in regulated industries. A safer tomorrow.",
	"IMPACT & BENEFITS  ·  A SAFER TOMORROW");
title("Real value, ", "higher control.");
[
	["01", "Conversational impact", ["Safer AI interactions", "Human oversight"], 0.6, 1.95, 3.71],
	["02", "Faster research", ["Private AI research", "Controlled experimentation"], 4.81, 1.95, 3.71],
	["03", "National impact", ["AI & data sovereignty", "Reduced external dependence"], 9.02, 1.95, 3.71],
	["04", "Technical impact", ["Local LLM + RAG", "Multi-agent orchestration", "Sandbox + verification", "Auditability"], 0.6, 4.55, 5.915],
	["05", "Economic & industrial impact", ["Lower recurring AI costs", "Secure enterprise adoption", "Regulated industries"], 6.815, 4.55, 5.915],
].forEach(([n, h, pts, x, y, w], i) => {
	const at = i * 200;
	card(DARK, x, y, w, 2.3, "up", at);
	text(n, { x: x + 0.3, y: y + 0.22, w: 1, h: 0.5, fontFace: SERIF, italic: true, fontSize: 26, color: C.accent2, valign: "middle" }, "up", at);
	text(h, { x: x + 0.3, y: y + 0.8, w: w - 0.6, h: 0.4, fontSize: 16, bold: true, color: C.background1, valign: "middle" }, "up", at);
	chips(DARK, x + 0.3, y + 1.35, w - 0.6, pts, "plain", at + 150);
});

// ================================================================= 8. FUTURE PROSPECTS (light)
startSlide(null,
	"Where it goes next: multimodal enterprise AI across vision, audio, video and complex documents; multi-site deployment with local AI at every site " +
	"and central governance; industry-specific agents for manufacturing, healthcare, finance, government and defence; continuous security and governance; " +
	"and finally an enterprise AI control layer - the secure orchestration and governance layer for enterprise AI.",
	"FUTURE PROSPECTS");
title("From workbench to ", "control layer.");
{
	const at = 0;
	cur.slide.addImage({ path: A("wave.png"), x: 0, y: 2.06, w: W, h: 0.694, objectName: nm("fade", at), altText: "" });
	shape(pres.ShapeType.rect, { x: 0, y: 2.75, w: W, h: 2.75, fill: { color: C.text1 } }, "fade", at);
	cur.slide.addImage({ path: A("wave-down.png"), x: 0, y: 5.5, w: W, h: 0.694, objectName: nm("fade", at), altText: "" });
	const steps = [
		["Multimodal enterprise AI", "Vision, audio, video & complex-document understanding"],
		["Multi-site deployment", "Local AI at every site with centralised governance"],
		["Industry-specific agents", "Manufacturing, healthcare, finance, government & defence"],
		["Continuous security & governance", "Policy enforcement, monitoring, audit & compliance"],
		["Enterprise AI control layer", "Evolve into the secure orchestration and governance layer for enterprise AI"],
	];
	const cxs = steps.map((_, i) => 1.9 + i * 2.38);
	stepper(DARK, cxs[0] - 0.08, 3.28, cxs[4] - cxs[0], steps.map(() => ({})), { dashed: true, highlight: 4, at: at + 300 });
	steps.forEach(([h, d], i) => {
		const sat = at + 300 + i * 160;
		text(`0${i + 1}`, { x: cxs[i] - 1.1, y: 2.86, w: 2.2, h: 0.34, fontFace: SERIF, italic: true, fontSize: 16, color: C.accent2, align: "center", valign: "middle" }, "up", sat);
		text(h, { x: cxs[i] - 1.1, y: 3.6, w: 2.2, h: 0.55, fontSize: 13.5, bold: true, color: C.background1, align: "center", valign: "middle" }, "up", sat);
		text(d, { x: cxs[i] - 1.1, y: 4.2, w: 2.2, h: 1.15, fontSize: 11.5, align: "center", ...DARK.muted }, "up", sat);
	});
}

// ================================================================= 9. RESEARCH & REFERENCES (dark)
startSlide("References",
	"Our work builds on transformer, retrieval-augmented generation, self-refinement and multi-agent research, and is backed by our own architecture, " +
	"verification and security documentation plus 2026 market research on inference economics and cloud versus on-prem TCO. The repository and the explanation videos are linked at the bottom.",
	"RESEARCH & REFERENCES");
title("Grounded in ", "research.");
const LNK = (t, url) => ({ t, url });
[
	["SUPPORTING RESEARCH PAPERS", "book", [
		LNK("Attention Is All You Need", "https://en.wikipedia.org/wiki/Attention_Is_All_You_Need"),
		LNK("Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", "http://arxiv.org/abs/2005.11401"),
		LNK("Self-Refine: Iterative Refinement with Self-Feedback", "http://arxiv.org/abs/2303.17651"),
		LNK("AutoGen: Next-Gen LLM Applications via Multi-Agent Conversation", "http://arxiv.org/abs/2308.08155"),
	]],
	["TECHNICAL DOCUMENTATION", "fileCode", [
		LNK("Sovereign AI Project Deep Research"), LNK("Master Architecture + Phase Specifications"),
		LNK("Verification Reports + Security Runbooks"), LNK("RUNNING.md + Sovereign Configuration"),
	]],
	["MARKET RESEARCH", "chart", [
		LNK("Inference Economics of Enterprise Coding Agents — 2026"), LNK("Hardware Economics: Cloud vs On-Prem TCO — 2026"),
		LNK("On-Premise vs Cloud: Generative AI TCO — 2026"),
	]],
].forEach(([h, ic, items], i) => {
	const x = COLS[i], at = i * 220;
	card(DARK, x, 1.95, CW, 3.35, "up", at);
	icon(ic, "lilac", x + 0.3, 2.22, 0.3, "up", at);
	label(DARK, h, x + 0.72, 2.24, CW - 1.0, "up", at);
	// a linked title is one linked run per word, so viewers that treat a link as one unbreakable field still wrap it
	const runs = items.flatMap((r, k) => {
		const words = r.url ? r.t.split(" ") : [r.t];
		return words.map((w, j) => ({
			text: j < words.length - 1 ? w + " " : w,
			options: { ...(r.url ? { hyperlink: { url: r.url }, color: C.background1 } : {}), breakLine: j === words.length - 1 && k < items.length - 1 },
		}));
	});
	text(runs, { x: x + 0.3, y: 2.8, w: CW - 0.6, h: 2.35, fontSize: 12.5, paraSpaceAfter: 7, ...DARK.muted }, "up", at + 100);
});
[
	["github", "GitHub repo", "github.com/Yash3510", "Open", "https://github.com/Yash3510/Multi-LLM-Agentic-Ai"],
	["play", "Demo video", "The 4CE chat, end to end", null, null],
	["play", "PPT video", "Narrated explanation", "Watch", "https://1drv.ms/p/c/1e7d8a4c6e729bdb/IQC%20ydx9YwLXVRqQyP9bNjAuyAdYZ7JEdsIa4ADd%208qzDv6HU?e=gWzcwv"],
].forEach(([ic, h, meta, btn, url], i) => fileCard(DARK, COLS[i], 5.55, CW, 1.3, ic, h, meta, btn, url, 700 + i * 150));

// ================================================================= 10. CLOSING (light)
startSlide("Close",
	"Your data stays yours. Sovereign, secure, verifiable, actionable: 4CE turns private organisational knowledge into actionable intelligence " +
	"and automates real workflows while keeping humans in control. Powerful enough for enterprises, controlled enough to trust. Thank you.");
text("4CE", { x: 6.37, y: 0.72, w: 2.4, h: 1.0, fontFace: HEAD, bold: true, fontSize: 64, charSpacing: -1.5, color: C.text1, valign: "middle" }, "fade", 0);
title("Your data ", "stays yours.", { x: 0.6, y: 2.0, w: 12.13, h: 0.95, fontSize: 46, align: "center" });
text("Sovereign. Secure. Verifiable. Actionable.", { x: 0.6, y: 3.0, w: 12.13, h: 0.4, fontSize: 17, align: "center", ...LIGHT.muted }, "up", 150);
[
	"Turns private organisational knowledge into actionable intelligence",
	"Automates real workflows while keeping humans in control",
].forEach((t, i) => {
	const y = 3.72 + i * 0.5, at = 350 + i * 180;
	checkbox(2.98, y + 0.03, 0.28, "zoom", at + 100);
	text(t, { x: 3.43, y, w: 7.1, h: 0.34, fontSize: 14.5, color: C.text1, valign: "middle" }, "up", at);
});
shape(pres.ShapeType.roundRect, { x: 2.67, y: 5.0, w: 8.0, h: 0.72, rectRadius: 0.36, fill: { color: C.background2 }, line: { color: C.accent2, width: 1.25 },
	shadow: { type: "outer", color: THEME.colors.accent1, opacity: 0.3, blur: 14, offset: 0, angle: 90 } }, "zoom", 800);
text([
	{ text: "Powerful enough for enterprises. ", options: { color: C.text1 } },
	{ text: "Controlled enough to trust.", options: { fontFace: SERIF, italic: true, color: C.accent1 } },
], { x: 2.67, y: 5.0, w: 8.0, h: 0.72, fontSize: 17, align: "center", valign: "middle" }, "zoom", 800);
text("THANK YOU  ·  TEAM KERN  ·  4CE (ACE)", { x: 0.6, y: 6.25, w: 12.13, h: 0.3, fontSize: 11, bold: true, charSpacing: 2, align: "center", ...LIGHT.muted }, "fade", 1100);

// ---------------------------------------------------------------- write
(async () => {
	await pres.writeFile({ fileName: OUT });
	fs.writeFileSync(path.join(path.dirname(OUT), "anim.json"), JSON.stringify(ANIM, null, 1));
	fs.writeFileSync(path.join(path.dirname(OUT), "theme.json"), JSON.stringify(THEME, null, 1));
	console.log("wrote", OUT);
})();
