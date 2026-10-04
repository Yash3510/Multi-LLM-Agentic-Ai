// Builds the Team Kern SIH 2026 deck. Every slide carries the same named "actors"
// (!!band, !!wheel, !!orbA-C, !!ghost, !!title) in new positions, so PowerPoint's Morph
// transition moves, resizes and spins them between slides. postprocess.py then adds the
// Morph transitions and the entrance animations listed in anim.json.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const OUT = process.argv[2] || path.join(__dirname, "deck.raw.pptx");
const A = (f) => path.join(__dirname, "assets", f);

const THEME = {
	name: "Sovereign Morph",
	headFontFace: "Arial Black",
	bodyFontFace: "Calibri",
	colors: {
		dk1: "011936", lt1: "FFFFFF", dk2: "0B2A55", lt2: "E8F1FF",
		accent1: "1D74FF", accent2: "1BDD96", accent3: "00B0F0", accent4: "6AC4E6",
		accent5: "2C7578", accent6: "FFB547", hlink: "6AC4E6", folHlink: "1BDD96",
	},
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Sovereign On-Premise Agentic AI Workbench";
pres.author = "Team Kern";
pres.subject = "Smart India Hackathon 2026 - SIH26117";
const C = pres.SchemeColor;
const HEAD = "+mj-lt";

pres.defineSlideMaster({ title: "Morph Navy", background: { color: THEME.colors.dk1 } });

// ---------------------------------------------------------------- morph actors
const ORBS = [
	["!!orbA", "orb-mint.png", 7.0],
	["!!orbB", "orb-blue.png", 6.0],
	["!!orbC", "orb-cyan.png", 4.5],
];
const STATES = [
	/* 1 title    */ { orbs: [[-4.2, -4.4], [8.6, 2.6], [1.5, 5.4]], ghost: [-0.8, 4.3], band: [6.55, 0.05, 7.4, 7.4, 3.7], wheel: [7.45, 0.95, 5.6, 270] },
	/* 2 solution */ { orbs: [[-3.8, -4.6], [7.2, 3.2], [-1.0, 5.2]], ghost: [6.4, -2.6], band: [0.6, 1.45, 12.13, 5.45, 0.45], wheel: [0.95, 1.75, 4.85, 0] },
	/* 3 why      */ { orbs: [[-3.0, 3.0], [9.8, 4.2], [10.0, -3.0]], ghost: [5.0, 4.6], band: [-0.45, -0.45, 5.05, 8.4, 0.45], wheel: [0.85, 4.05, 2.85, 90] },
	/* 4 tech     */ { orbs: [[-3.6, 2.8], [3.8, 4.8], [5.0, -3.4]], ghost: [-1.2, 5.0], band: [8.85, -0.45, 4.95, 8.4, 0.45], wheel: [11.25, 6.15, 3.2, 180] },
	/* 5 risk     */ { orbs: [[-4.4, -3.0], [1.0, 4.9], [10.2, -3.3]], ghost: [-0.4, 5.0], band: [6.95, 1.4, 5.78, 5.55, 0.35], wheel: [11.85, 0.3, 0.95, 270] },
	/* 6 economy  */ { orbs: [[-3.8, -4.2], [8.4, -4.0], [10.8, 0.4]], ghost: [4.4, 4.2], band: [-0.45, 3.95, 14.23, 4.0, 0.6], wheel: [11.85, 0.3, 0.95, 0] },
	/* 7 impact   */ { orbs: [[3.17, 0.25], [-3.4, 3.8], [11.0, 4.2]], ghost: [7.6, 5.0], band: [4.917, 2.0, 3.5, 3.5, 1.75], wheel: [5.292, 2.375, 2.75, 90] },
	/* 8 future   */ { orbs: [[-3.0, 0.3], [9.0, -3.6], [5.0, 5.0]], ghost: [2.6, 5.1], band: [0.6, 3.8, 12.13, 0.5, 0.25], wheel: [0.45, 3.4, 1.3, 180] },
	/* 9 refs     */ { orbs: [[-4.0, -4.2], [9.6, -3.8], [-1.6, 5.2]], ghost: [5.4, -2.7], band: [0.6, 5.6, 12.13, 1.05, 0.525], wheel: [11.85, 0.3, 0.95, 270] },
	/* 10 close   */ { orbs: [[3.0, 0.3], [8.6, 2.4], [0.4, 4.2]], ghost: [2.0, 1.8], band: [0, 0, 13.333, 7.5, 0.01], wheel: [7.5, 1.0, 5.5, 0] },
];

const ANIM = [];
let cur = null;

function startSlide(section, notes) {
	if (section) pres.addSection({ title: section });
	const slide = pres.addSlide({ masterName: "Morph Navy", sectionTitle: section || cur.section });
	const idx = cur ? cur.idx + 1 : 1;
	cur = { slide, idx, n: 0, anims: [], section: section || cur.section };
	ANIM.push({ slide: idx, items: cur.anims });
	const st = STATES[idx - 1];

	ORBS.forEach(([name, file, size], i) => {
		const [x, y] = st.orbs[i];
		slide.addImage({ path: A(file), x, y, w: size, h: size, objectName: name, altText: "" });
	});
	slide.addText("4CE", {
		isTextBox: true, objectName: "!!ghost", x: st.ghost[0], y: st.ghost[1], w: 9.6, h: 3.8, margin: 0,
		fontFace: HEAD, fontSize: 250, color: C.text2, transparency: 35, valign: "middle",
	});
	const [bx, by, bw, bh, br] = st.band;
	slide.addShape(pres.ShapeType.roundRect, {
		objectName: "!!band", x: bx, y: by, w: bw, h: bh, rectRadius: br, fill: { color: C.accent1 },
		shadow: { type: "outer", color: "000000", opacity: 0.35, blur: 18, offset: 6, angle: 90 },
	});
	const [wx, wy, ws, wr] = st.wheel;
	slide.addImage({
		path: A("wheel.png"), x: wx, y: wy, w: ws, h: ws, rotate: wr, objectName: "!!wheel",
		altText: "Wheel of the four pillars: sovereignty, ingestion, governance, trust",
	});
	if (notes) slide.addNotes(notes);
	return slide;
}

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
// Icon centred in a filled circle - the deck's recurring badge.
function badge(iconName, x, y, d, fill, tone, fx, at) {
	shape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: fill } }, fx, at);
	const s = d * 0.56;
	icon(iconName, tone, x + (d - s) / 2, y + (d - s) / 2, s, fx, at);
}
function title(t, o = {}) {
	text(t, {
		objectName: "!!title", x: 0.6, y: 0.42, w: 9.8, h: 0.75, fontFace: HEAD, fontSize: 30,
		color: C.accent2, valign: "middle", ...o,
	});
}
const card = (x, y, w, h, fill, fx, at, extra = {}) =>
	shape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.14, fill, ...extra }, fx, at);

// ================================================================= 1. TITLE
startSlide("Opening",
	"Smart India Hackathon 2026, problem statement SIH26117: a sovereign, on-premise agentic AI workbench " +
	"that runs open-weight multimodal LLMs on confidential industrial data. Theme Smart Automation, category Software. " +
	"We are Team Kern, and the project is 4CE (ACE).");
shape(pres.ShapeType.roundRect, { x: 0.6, y: 1.0, w: 3.75, h: 0.46, rectRadius: 0.23, fill: { color: C.accent2, transparency: 85 }, line: { color: C.accent2, width: 1 } }, "up", 0);
text("SMART INDIA HACKATHON 2026", { x: 0.6, y: 1.0, w: 3.75, h: 0.46, fontSize: 13, bold: true, color: C.accent2, charSpacing: 2, align: "center", valign: "middle" }, "up", 0);
title("SOVEREIGN", { x: 0.6, y: 1.72, w: 6.2, h: 1.1, fontSize: 60 });
text("AGENTIC AI WORKBENCH", { x: 0.6, y: 2.85, w: 6.0, h: 0.6, fontFace: HEAD, fontSize: 26, color: C.background1, valign: "middle" }, "up", 150);
text("Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work",
	{ x: 0.6, y: 3.6, w: 5.75, h: 0.8, fontSize: 16, color: C.accent4 }, "up", 300);
[["PS ID", "SIH26117"], ["THEME", "Smart Automation"], ["CATEGORY", "Software"]].forEach(([k, v], i) => {
	const x = 0.6 + i * 1.97;
	card(x, 4.62, 1.85, 0.8, { color: C.text2 }, "up", 450 + i * 120);
	text(k, { x: x + 0.18, y: 4.7, w: 1.6, h: 0.28, fontSize: 11, bold: true, color: C.accent4, charSpacing: 2 }, "up", 450 + i * 120);
	text(v, { x: x + 0.18, y: 4.98, w: 1.62, h: 0.34, fontSize: 15, bold: true, color: C.background1 }, "up", 450 + i * 120);
});
text([
	{ text: "TEAM KERN", options: { color: C.background1 } },
	{ text: "   |   ", options: { color: C.accent4 } },
	{ text: "4CE (ACE)", options: { color: C.accent2 } },
], { x: 0.6, y: 5.75, w: 5.8, h: 0.5, fontFace: HEAD, fontSize: 20, valign: "middle" }, "up", 850);

// ================================================================= 2. OUR SOLUTION
startSlide("Solution",
	"Our solution rests on four pillars. Sovereignty: local LLMs, so data stays inside. Ingestion: legacy files become usable intelligence. " +
	"Governance: tool execution waits for human approval. Trust: every generated answer is source-verified.");
title("OUR SOLUTION");
[
	["SOVEREIGNTY", "Local LLMs  →  data stays inside", "shield"],
	["INGESTION", "Legacy files  →  usable intelligence", "fileIn"],
	["GOVERNANCE", "Tool execution  →  human approval", "userCheck"],
	["TRUST", "Generated answer  →  source-verified", "badge"],
].forEach(([h, d, ic], i) => {
	const y = 1.72 + i * 1.28, at = i * 160;
	card(6.2, y, 6.2, 1.08, { color: C.background1, transparency: 86 }, "up", at);
	badge(ic, 6.4, y + 0.19, 0.7, C.background1, "blue", "zoom", at + 200);
	text(h, { x: 7.35, y: y + 0.14, w: 4.9, h: 0.4, fontFace: HEAD, fontSize: 16, color: C.background1, charSpacing: 1 }, "up", at);
	text(d, { x: 7.35, y: y + 0.56, w: 4.9, h: 0.38, fontSize: 16, color: C.background2 }, "up", at);
});

// ================================================================= 3. WHY DIFFERENT
startSlide(null,
	"Why it is different. Generated code never runs on the host: it goes to an isolated sandbox for controlled execution. " +
	"Every action passes a central control layer for authorization, and sensitive actions need a human to approve them. " +
	"The architecture is model-independent: Qwen, Gemma, Mistral or another open model - change the model, not the architecture.");
title("WHY\nDIFFERENT", { x: 0.6, y: 0.75, w: 3.8, h: 1.6, fontSize: 34, color: C.background1, valign: "top" });
text("Three design choices make agentic AI safe to run on confidential data.",
	{ x: 0.6, y: 2.55, w: 3.6, h: 1.0, fontSize: 17, color: C.background2 }, "up", 100);

function chips(x, y, items, arrows, at) {
	let cx = x;
	items.forEach((t, i) => {
		const w = t.length * 0.088 + 0.36;
		shape(pres.ShapeType.roundRect, { x: cx, y, w, h: 0.42, rectRadius: 0.21, fill: { color: C.accent1 } }, "wipe", at + i * 140);
		text(t, { x: cx, y, w, h: 0.42, fontSize: 13, bold: true, color: C.background1, align: "center", valign: "middle" }, "wipe", at + i * 140);
		cx += w;
		if (i < items.length - 1) {
			if (arrows) {
				text("→", { x: cx, y, w: 0.38, h: 0.42, fontSize: 18, bold: true, color: C.accent2, align: "center", valign: "middle" }, "wipe", at + i * 140 + 70);
				cx += 0.38;
			} else cx += 0.15;
		}
	});
}
const WX = 5.1, WW = 7.63;
// card 1
card(WX, 0.55, WW, 1.7, { color: C.text2 }, "up", 200);
badge("box", WX + 0.3, 0.75, 0.62, C.accent2, "navy", "zoom", 350);
text("Isolated sandbox execution", { x: WX + 1.1, y: 0.78, w: 6.2, h: 0.55, fontSize: 19, bold: true, color: C.background1, valign: "middle" }, "up", 200);
chips(WX + 0.3, 1.55, ["AI-generated code", "Isolated environment", "Controlled execution"], true, 500);
// card 2
card(WX, 2.5, WW, 2.15, { color: C.text2 }, "up", 900);
badge("sliders", WX + 0.3, 2.7, 0.62, C.accent2, "navy", "zoom", 1050);
text("Centralised AI control", { x: WX + 1.1, y: 2.73, w: 6.2, h: 0.55, fontSize: 19, bold: true, color: C.background1, valign: "middle" }, "up", 900);
chips(WX + 0.3, 3.5, ["Every action", "Control layer", "Authorization", "Execution"], true, 1200);
icon("lock", "mint", WX + 0.32, 4.1, 0.32, "up", 1800);
text("Sensitive actions  →  mandatory human approval", { x: WX + 0.75, y: 4.06, w: 6.5, h: 0.4, fontSize: 15, bold: true, color: C.accent2, valign: "middle" }, "up", 1800);
// card 3
card(WX, 4.9, WW, 1.95, { color: C.text2 }, "up", 2000);
badge("cpu", WX + 0.3, 5.1, 0.62, C.accent2, "navy", "zoom", 2150);
text("Model-independent architecture", { x: WX + 1.1, y: 5.13, w: 6.2, h: 0.55, fontSize: 19, bold: true, color: C.background1, valign: "middle" }, "up", 2000);
chips(WX + 0.3, 5.88, ["Qwen", "Gemma", "Mistral", "Other open-source models"], false, 2300);
text("Change the model, not the architecture.", { x: WX + 0.3, y: 6.38, w: 6.8, h: 0.38, fontSize: 15, italic: true, color: C.accent4, valign: "middle" }, "up", 2850);

// ================================================================= 4. TECHNICAL APPROACH
startSlide("Technical",
	"Technical approach. Python and Bash at the core; FastAPI, Uvicorn, Socket.io and SvelteKit with JWT session auth for the platform; " +
	"Bionic with Qwen and Gemma models and nomic-embed-text v1.5 embeddings for AI; SQLite and ChromaDB for storage; " +
	"Docker with hardening flags for isolated execution; python-docx for document generation; and a custom test harness. " +
	"Over 75 percent of the prototype is complete, and the code is on GitHub.");
title("TECHNICAL APPROACH");
const STACK = [
	["Language & runtime", "Python  ·  Bash", "code"],
	["Application platform", "FastAPI · Uvicorn · Socket.io · SvelteKit · JWT session auth", "server"],
	["AI / ML", "Bionic · Qwen models · Gemma models · nomic-embed-text-v1.5", "brain"],
	["Data & storage", "SQLite  ·  ChromaDB", "database"],
	["Execution & isolation", "Docker  ·  hardening flags", "docker"],
	["Document generation", "python-docx", "fileText"],
	["Deployment & tooling", "Custom test harness", "wrench"],
];
STACK.forEach(([h, d, ic], i) => {
	const full = i === 6;
	const col = i % 2, row = Math.floor(i / 2);
	const x = 0.6 + (full ? 0 : col * 4.05), y = 1.45 + row * 1.38, w = full ? 7.85 : 3.8;
	const at = i * 110;
	card(x, y, w, 1.2, { color: C.text2 }, "up", at);
	badge(ic, x + 0.22, y + 0.3, 0.6, C.accent1, "white", "zoom", at + 150);
	text(h, { x: x + 1.0, y: y + 0.16, w: w - 1.2, h: 0.36, fontSize: 15, bold: true, color: C.background1, valign: "middle" }, "up", at);
	text(d, { x: x + 1.0, y: y + 0.55, w: w - 1.15, h: 0.56, fontSize: 13, color: C.accent4 }, "up", at);
});
text("BUILD STATUS", { x: 9.35, y: 0.75, w: 3.5, h: 0.35, fontSize: 13, bold: true, color: C.background1, charSpacing: 3 }, "up", 300);
cur.slide.addChart(pres.ChartType.doughnut, [{ name: "Prototype", labels: ["Completed", "Remaining"], values: [75, 25] }], {
	x: 9.5, y: 1.2, w: 3.2, h: 3.2, holeSize: 72, chartColors: ["FFFFFF", "0B2A55"],
	showLegend: false, showValue: false, showPercent: false, showLabel: false, showTitle: false,
	dataBorder: { pt: 0, color: "1D74FF" }, objectName: nm("zoom", 450),
	altText: "Doughnut chart: over 75 percent of the prototype completed",
});
text("75%+", { x: 9.5, y: 2.42, w: 3.2, h: 0.75, fontFace: HEAD, fontSize: 30, color: C.background1, align: "center", valign: "middle" }, "zoom", 750);
text("of the prototype is already built", { x: 9.35, y: 4.55, w: 3.6, h: 0.65, fontSize: 16, color: C.background2, align: "center" }, "up", 900);
shape(pres.ShapeType.roundRect, { x: 9.4, y: 5.38, w: 3.5, h: 0.6, rectRadius: 0.3, fill: { color: C.background1 } }, "up", 1050);
icon("github", "navy", 9.65, 5.52, 0.32, "up", 1050);
text([{ text: "View the GitHub repo", options: { hyperlink: { url: "https://github.com/Yash3510/Multi-LLM-Agentic-Ai" }, color: C.text1 } }],
	{ x: 10.1, y: 5.38, w: 2.7, h: 0.6, fontSize: 15, bold: true, color: C.text1, valign: "middle" }, "up", 1050);

// ================================================================= 5. FEASIBILITY - RISK
startSlide("Feasibility",
	"Feasibility: each real risk we hit has a mitigation. Cloud dependency - solved with a local-only stack and outbound paths disabled. " +
	"A 65K context overflowed 6 GB of VRAM and fell back to CPU with 20-plus-minute inference; an 8K context fits VRAM and restores GPU inference. " +
	"Hallucinated findings are caught by ULTRON verification with bounded replanning. Generated code runs only in a hardened Docker sandbox.");
title("FEASIBILITY & VIABILITY");
text("RISK", { x: 0.6, y: 1.55, w: 3, h: 0.35, fontSize: 14, bold: true, color: C.accent4, charSpacing: 3 }, "up", 0);
text("MITIGATION", { x: 7.45, y: 1.55, w: 3, h: 0.35, fontSize: 14, bold: true, color: C.background1, charSpacing: 3 }, "up", 0);
[
	["Cloud dependency", "Data could leave the enterprise", "Local-only stack + outbound paths disabled"],
	["65K context window", "KV cache exceeded 6 GB VRAM → CPU fallback → 20+ min inference", "8K context fits VRAM → GPU inference restored"],
	["AI hallucination", "Generated findings could be incorrect", "ULTRON verification + bounded replan"],
	["Generated-code risk", "AI code could reach the host or network", "Hardened Docker sandbox → isolated execution"],
].forEach(([p, pd, s], i) => {
	const y = 2.05 + i * 1.18, at = 150 + i * 260;
	card(0.6, y, 6.0, 1.0, { color: C.text2 }, "up", at);
	text([
		{ text: p, options: { bold: true, color: C.background1, fontSize: 16, breakLine: true } },
		{ text: pd, options: { color: C.accent4, fontSize: 14 } },
	], { x: 0.85, y, w: 5.35, h: 1.0, valign: "middle" }, "up", at);
	badge("arrow", 6.67, y + 0.22, 0.56, C.accent2, "navy", "zoom", at + 120);
	text(s, { x: 7.45, y, w: 5.05, h: 1.0, fontSize: 16, bold: true, color: C.background1, valign: "middle" }, "wipe", at + 180);
});

// ================================================================= 6. VIABILITY - RESOURCES & ECONOMICS
startSlide(null,
	"What it takes to run: local compute with a GPU recommended, Docker and a local model server, persistent storage next to the enterprise data, " +
	"and proven frameworks. How it pays: potentially lower recurring AI costs for sustained, high-volume workloads; " +
	"monetisation through enterprise licensing plus setup and integration; and recurring revenue from support, maintenance and custom agents.");
title("RESOURCES & ECONOMICS");
text("RESOURCE REQUIREMENTS", { x: 0.6, y: 1.35, w: 6, h: 0.35, fontSize: 14, bold: true, color: C.accent4, charSpacing: 3 }, "up", 0);
[
	["Local compute + GPU (recommended)", "cpu"],
	["Docker + local model server", "docker"],
	["Persistent storage + enterprise data", "hardDrive"],
	["Proven frameworks", "layers"],
].forEach(([t, ic], i) => {
	const x = 0.6 + i * 3.095, at = 100 + i * 140;
	card(x, 1.8, 2.845, 1.75, { color: C.text2 }, "up", at);
	badge(ic, x + 0.25, 2.02, 0.68, C.accent1, "white", "zoom", at + 150);
	text(t, { x: x + 0.25, y: 2.82, w: 2.4, h: 0.62, fontSize: 15, bold: true, color: C.background1 }, "up", at);
});
text("ECONOMIC APPROACH", { x: 0.6, y: 4.3, w: 6, h: 0.35, fontSize: 14, bold: true, color: C.background1, charSpacing: 3 }, "up", 700);
[
	["Lower recurring AI costs", "Potentially lower costs for sustained, high-volume workloads", "trendDown"],
	["Enterprise licensing", "Monetised through licensing plus setup and integration", "briefcase"],
	["Recurring revenue", "Support, maintenance and custom agents", "repeat"],
].forEach(([h, d, ic], i) => {
	const x = 0.6 + i * 4.127, at = 850 + i * 160;
	card(x, 4.78, 3.877, 1.85, { color: C.background1 }, "fly", at);
	badge(ic, x + 0.25, 5.0, 0.65, C.accent1, "white", "fly", at);
	text(h, { x: x + 1.05, y: 5.0, w: 2.7, h: 0.65, fontSize: 17, bold: true, color: C.text1, valign: "middle" }, "fly", at);
	text(d, { x: x + 0.25, y: 5.8, w: 3.4, h: 0.72, fontSize: 15, color: C.text2 }, "fly", at);
});

// ================================================================= 7. IMPACT
startSlide("Impact",
	"Impact and benefits. Conversational: safer AI interactions with human oversight. Research: private AI research and controlled experimentation on sensitive data. " +
	"National: AI and data sovereignty with less external dependence. Technical: local LLM plus RAG, multi-agent orchestration, sandboxing, verification and auditability. " +
	"Economic and industrial: lower recurring AI costs and secure adoption in regulated industries.");
title("IMPACT & BENEFITS");
text("Real value, higher control, a safer tomorrow.", { x: 6.4, y: 0.42, w: 6.33, h: 0.75, fontSize: 16, italic: true, color: C.accent4, align: "right", valign: "middle" }, "up", 0);
const IMPACT = [
	["01", "CONVERSATIONAL IMPACT", ["Safer AI interactions", "Human oversight"], 0.6, 1.5],
	["02", "FASTER RESEARCH", ["Private AI research", "Controlled experimentation"], 8.733, 1.5],
	["03", "NATIONAL IMPACT", ["AI & data sovereignty", "Reduced external dependence"], 0.6, 3.55],
	["04", "TECHNICAL IMPACT", ["Local LLM + RAG", "Multi-agent orchestration", "Sandbox + verification · auditability"], 8.733, 3.55],
];
IMPACT.forEach(([n, h, pts, x, y], i) => {
	const at = 150 + i * 220;
	card(x, y, 4.0, 1.7, { color: C.text2 }, "up", at);
	text(n, { x: x + 0.25, y: y + 0.2, w: 0.75, h: 0.45, fontFace: HEAD, fontSize: 22, color: C.accent2, valign: "middle" }, "up", at);
	text(h, { x: x + 1.0, y: y + 0.2, w: 2.85, h: 0.45, fontSize: 16, bold: true, color: C.background1, valign: "middle" }, "up", at);
	text(pts.map((p, k) => ({ text: p, options: { bullet: { indent: 14 }, breakLine: k < pts.length - 1 } })),
		{ x: x + 0.25, y: y + 0.75, w: 3.6, h: 0.85, fontSize: 14, color: C.accent4, paraSpaceAfter: 2 }, "up", at);
});
card(4.17, 5.8, 5.0, 1.2, { color: C.text2 }, "up", 1050);
text("05", { x: 4.42, y: 5.92, w: 0.75, h: 0.42, fontFace: HEAD, fontSize: 22, color: C.accent2, valign: "middle" }, "up", 1050);
text("ECONOMIC & INDUSTRIAL IMPACT", { x: 5.17, y: 5.92, w: 3.85, h: 0.42, fontSize: 16, bold: true, color: C.background1, valign: "middle" }, "up", 1050);
text("Lower recurring AI costs · secure enterprise adoption · regulated industries",
	{ x: 4.42, y: 6.38, w: 4.6, h: 0.55, fontSize: 14, color: C.accent4 }, "up", 1050);

// ================================================================= 8. FUTURE PROSPECTS
startSlide(null,
	"Where it goes next: multimodal enterprise AI across vision, audio, video and complex documents; multi-site deployment with local AI at every site " +
	"and central governance; industry-specific agents for manufacturing, healthcare, finance, government and defence; continuous security and governance; " +
	"and finally an enterprise AI control layer - the secure orchestration and governance layer for enterprise AI.");
title("FUTURE PROSPECTS");
const FUTURE = [
	["Multimodal enterprise AI", "Vision, audio, video & complex-document understanding", "eye"],
	["Multi-site deployment", "Local AI at every site with centralised governance", "building"],
	["Industry-specific agents", "Manufacturing, healthcare, finance, government & defence", "bot"],
	["Continuous security & governance", "Policy enforcement, monitoring, audit & compliance", "shield"],
	["Enterprise AI control layer", "Evolve into the secure orchestration and governance layer for enterprise AI", "layers"],
];
FUTURE.forEach(([h, d, ic], i) => {
	const cx = 2.6 + i * 2.1, above = i % 2 === 0, at = 100 + i * 260;
	const bw = 3.3, bx = cx - bw / 2;
	badge(ic, cx - 0.42, 3.63, 0.84, C.accent2, "navy", "zoom", at);
	shape(pres.ShapeType.line, above
		? { x: cx, y: 3.25, w: 0, h: 0.38, line: { color: C.accent2, width: 1.5 } }
		: { x: cx, y: 4.47, w: 0, h: 0.38, line: { color: C.accent2, width: 1.5 } }, "fade", at + 150);
	text([
		{ text: h, options: { bold: true, fontSize: 16, color: C.background1, breakLine: true } },
		{ text: d, options: { fontSize: 14, color: C.accent4 } },
	], { x: bx, y: above ? 1.65 : 4.9, w: bw, h: 1.55, align: "center", valign: above ? "bottom" : "top" }, "up", at + 150);
});

// ================================================================= 9. RESEARCH & REFERENCES
startSlide("References",
	"Our work builds on transformer, retrieval-augmented generation, self-refinement and multi-agent research, and is backed by our own " +
	"architecture, verification and security documentation plus 2026 market research on inference economics and cloud versus on-prem TCO. " +
	"Links to the GitHub repo and the explanation videos are at the bottom.");
title("RESEARCH & REFERENCES");
const L = (t, url) => ({ text: t, options: url ? { hyperlink: { url } } : {} });
const REFS = [
	["SUPPORTING RESEARCH PAPERS", "book", [
		L("Attention Is All You Need", "https://en.wikipedia.org/wiki/Attention_Is_All_You_Need"),
		L("Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", "http://arxiv.org/abs/2005.11401"),
		L("Self-Refine: Iterative Refinement with Self-Feedback", "http://arxiv.org/abs/2303.17651"),
		L("AutoGen: Next-Gen LLM Applications via Multi-Agent Conversation", "http://arxiv.org/abs/2308.08155"),
	]],
	["TECHNICAL DOCUMENTATION", "fileCode", [
		L("Sovereign AI Project Deep Research"),
		L("Master Architecture + Phase Specifications"),
		L("Verification Reports + Security Runbooks"),
		L("RUNNING.md + Sovereign Configuration"),
	]],
	["MARKET RESEARCH", "chart", [
		L("Inference Economics of Enterprise Coding Agents — 2026"),
		L("Hardware Economics: Cloud vs On-Prem TCO — 2026"),
		L("On-Premise vs Cloud: Generative AI TCO — 2026"),
	]],
];
REFS.forEach(([h, ic, items], i) => {
	const x = 0.6 + i * 4.21, at = i * 220;
	card(x, 1.45, 3.71, 3.75, { color: C.text2 }, "up", at);
	badge(ic, x + 0.25, 1.68, 0.6, C.accent1, "white", "zoom", at + 150);
	text(h, { x: x + 1.0, y: 1.66, w: 2.55, h: 0.64, fontSize: 14, bold: true, color: C.background1, charSpacing: 1, valign: "middle" }, "up", at);
	// A linked title is split into one linked run per word: some viewers treat a link as a single
	// unbreakable field and would otherwise wrap it mid-word.
	const runs = items.flatMap((r, k) => {
		const words = r.options.hyperlink ? r.text.split(" ") : [r.text];
		return words.map((w, j) => ({
			text: j < words.length - 1 ? w + " " : w,
			options: { ...r.options, breakLine: j === words.length - 1 && k < items.length - 1 },
		}));
	});
	text(runs, { x: x + 0.25, y: 2.5, w: 3.25, h: 2.55, fontSize: 15, color: C.background2, paraSpaceAfter: 10 }, "up", at + 100);
});
text("LINKS", { x: 1.05, y: 5.6, w: 1.3, h: 1.05, fontSize: 15, bold: true, color: C.background1, charSpacing: 3, valign: "middle" }, "fade", 700);
[
	["GitHub repo", "github", "https://github.com/Yash3510/Multi-LLM-Agentic-Ai"],
	["Demo video", "play", null],
	["PPT video explanation", "play", "https://1drv.ms/p/c/1e7d8a4c6e729bdb/IQC%20ydx9YwLXVRqQyP9bNjAuyAdYZ7JEdsIa4ADd%208qzDv6HU?e=gWzcwv"],
].forEach(([t, ic, url], i) => {
	const x = 2.45 + i * 3.4, at = 800 + i * 150;
	shape(pres.ShapeType.roundRect, { x, y: 5.845, w: 3.1, h: 0.56, rectRadius: 0.28, fill: { color: C.background1 } }, "zoom", at);
	icon(ic, "blue", x + 0.22, 5.965, 0.32, "zoom", at);
	text([{ text: t, options: url ? { hyperlink: { url }, color: C.text1 } : {} }],
		{ x: x + 0.65, y: 5.845, w: 2.35, h: 0.56, fontSize: 15, bold: true, color: C.text1, valign: "middle" }, "zoom", at);
});

// ================================================================= 10. CLOSING
startSlide("Close",
	"Your data stays yours. Sovereign, secure, verifiable, actionable: it turns private organisational knowledge into actionable intelligence " +
	"and automates real workflows while keeping humans in control. Powerful enough for enterprises, controlled enough to trust. Thank you.");
title("YOUR DATA\nSTAYS YOURS", { x: 0.6, y: 1.0, w: 6.6, h: 2.2, fontSize: 48, color: C.background1, valign: "top" });
text("Sovereign. Secure. Verifiable. Actionable.", { x: 0.6, y: 3.35, w: 6.6, h: 0.5, fontSize: 21, bold: true, color: C.text1 }, "up", 100);
text([
	{ text: "Turns private organisational knowledge into actionable intelligence.", options: { bullet: { indent: 16 }, breakLine: true } },
	{ text: "Automates real workflows while keeping humans in control.", options: { bullet: { indent: 16 } } },
], { x: 0.6, y: 3.95, w: 6.4, h: 0.95, fontSize: 16, color: C.background1, paraSpaceAfter: 4 }, "up", 300);
text("Powerful enough for enterprises. Controlled enough to trust.", { x: 0.6, y: 5.0, w: 6.4, h: 0.45, fontSize: 16, italic: true, color: C.background2 }, "up", 500);
shape(pres.ShapeType.roundRect, { x: 0.6, y: 5.75, w: 5.2, h: 0.7, rectRadius: 0.35, fill: { color: C.text1 } }, "fly", 700);
text([
	{ text: "THANK YOU", options: { fontFace: HEAD, color: C.accent2 } },
	{ text: "   Team Kern · 4CE (ACE)", options: { bold: true, color: C.background1 } },
], { x: 0.85, y: 5.75, w: 4.9, h: 0.7, fontSize: 17, valign: "middle" }, "fly", 700);

// ---------------------------------------------------------------- write
(async () => {
	await pres.writeFile({ fileName: OUT });
	fs.writeFileSync(path.join(path.dirname(OUT), "anim.json"), JSON.stringify(ANIM, null, 1));
	fs.writeFileSync(path.join(path.dirname(OUT), "theme.json"), JSON.stringify(THEME, null, 1));
	console.log("wrote", OUT);
})();
