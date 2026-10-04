// Renders the deck as one self-contained HTML file - a fallback for presenting from a browser
// when PowerPoint is missing or misbehaves. It loads build.cjs against a stand-in for pptxgenjs
// that records every shape, then draws the same slides with the same motion: the shared
// "!!" shapes glide between slides as Morph does, and content builds in once they land.
// Fonts, icons and images are embedded, so the file works offline.
//
//   node html.cjs deck.html
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");

const OUT = process.argv[2] || path.join(__dirname, "deck.html");
const ROOT = path.join(__dirname, "..", "..");

// ---------------------------------------------------------------- stand-in for pptxgenjs
class Recorder {
	constructor() {
		Recorder.instance = this;
		this.slides = [];
		this.SchemeColor = {
			text1: "tx1", text2: "tx2", background1: "bg1", background2: "bg2",
			accent1: "accent1", accent2: "accent2", accent3: "accent3", accent4: "accent4", accent5: "accent5", accent6: "accent6",
		};
		this.ShapeType = { roundRect: "roundRect", rect: "rect", ellipse: "ellipse", line: "line", custGeom: "custGeom" };
	}
	defineSlideMaster(m) { this.master = m; }
	addSection() {}
	addSlide() {
		const s = { items: [], notes: "" };
		s.addText = (t, o) => s.items.push({ kind: "text", t, o });
		s.addShape = (type, o) => s.items.push({ kind: "shape", type, o });
		s.addImage = (o) => s.items.push({ kind: "image", o });
		s.addNotes = (n) => { s.notes = n; };
		this.slides.push(s);
		return s;
	}
	async writeFile() {}
}
const pptxId = require.resolve("pptxgenjs");
require.cache[pptxId] = { id: pptxId, filename: pptxId, loaded: true, exports: Recorder };
const { ANIM, THEME, MORPH_MS } = require("./build.cjs");
const deck = Recorder.instance;

// ---------------------------------------------------------------- units and colours
const PX = 100; // px per inch: the stage is 1333 x 750 px and is scaled to the window
const PT = PX / 72;
const n = (v) => +(v).toFixed(2);
const SLOT = { tx1: "dk1", tx2: "dk2", bg1: "lt1", bg2: "lt2" };
function rgba(c, transparency = 0) {
	const h = THEME.colors[SLOT[c] || c] || c;
	const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
	return transparency ? `rgba(${r},${g},${b},${n(1 - transparency / 100)})` : `#${h}`;
}
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const MONO_STACK = `'JetBrains Mono', ui-monospace, monospace`;
const font = (face) => (face === "JetBrains Mono" ? MONO_STACK : null); // anything else is the theme's Inter

// ---------------------------------------------------------------- assets
const assets = new Map(); // file -> css class
function assetClass(file) {
	if (!assets.has(file)) assets.set(file, `a${assets.size}`);
	return assets.get(file);
}

// ---------------------------------------------------------------- shapes
function box(o) {
	return `left:${n(o.x * PX)}px;top:${n(o.y * PX)}px;width:${n(o.w * PX)}px;height:${n(o.h * PX)}px;`;
}
function shapeStyle(type, o) {
	let s = box(o);
	if (type === "roundRect") s += `border-radius:${n(Math.min((o.rectRadius || 0) * PX, (Math.min(o.w, o.h) * PX) / 2))}px;`;
	if (type === "ellipse") s += "border-radius:50%;";
	if (o.fill && type !== "custGeom") s += `background:${rgba(o.fill.color, o.fill.transparency)};`;
	if (o.line && type !== "line") s += `border:${n((o.line.width || 0.75) * PT)}px solid ${rgba(o.line.color, o.line.transparency)};`;
	if (o.shadow) {
		const off = (o.shadow.offset || 0) * PT;
		const hex = o.shadow.color.length === 6 ? o.shadow.color : THEME.colors[o.shadow.color];
		const [r, g, b] = [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16));
		s += `box-shadow:0 ${n(off)}px ${n((o.shadow.blur || 0) * PT)}px rgba(${r},${g},${b},${o.shadow.opacity});`;
	}
	if (o.rotate) s += `transform:rotate(${o.rotate}deg);`;
	return s;
}
function pathData(points, w, h) {
	return points.map((p) => (p.close ? "Z" : `${p.moveTo ? "M" : "L"}${n((p.x / w) * 1000)} ${n((p.y / h) * 1000)}`)).join("");
}
function renderShape(type, o, attrs, css = "") {
	if (type === "line") {
		const dash = o.line.dashType ? "dashed" : "solid";
		const lw = n((o.line.width || 0.75) * PT);
		const edge = o.h === 0 ? "border-top" : "border-left";
		return `<div ${attrs} class="el" style="${css}${box(o)}${edge}:${lw}px ${dash} ${rgba(o.line.color, o.line.transparency)};height:${o.h === 0 ? 0 : n(o.h * PX)}px"></div>`;
	}
	if (type === "custGeom") {
		return `<svg ${attrs} class="el" viewBox="0 0 1000 1000" preserveAspectRatio="none" style="${css}${shapeStyle(type, o)}color:${rgba(o.fill.color)}"><path fill="currentColor" fill-rule="evenodd" d="${pathData(o.points, o.w, o.h)}"/></svg>`;
	}
	return `<div ${attrs} class="el" style="${css}${shapeStyle(type, o)}"></div>`;
}

// ---------------------------------------------------------------- text
// pptxgenjs semantics: "\n" and breakLine end a paragraph; a run that carries `bullet` starts one.
function paragraphs(t) {
	const runs = (typeof t === "string" ? [{ text: t, options: {} }] : t).flatMap((r) =>
		String(r.text).split("\n").map((part, i, all) => ({ text: part, options: { ...(r.options || {}), breakLine: i < all.length - 1 ? true : (r.options || {}).breakLine } })));
	const paras = [[]];
	runs.forEach((r) => {
		if (r.options.bullet && paras[paras.length - 1].length) paras.push([]);
		paras[paras.length - 1].push(r);
		if (r.options.breakLine) paras.push([]);
	});
	return paras.filter((p, i) => p.length || i === 0);
}
function renderText(t, o, attrs, css = "") {
	const just = { top: "flex-start", middle: "center", bottom: "flex-end" }[o.valign || "top"];
	let s = box(o) + `justify-content:${just};text-align:${o.align || "left"};font-size:${n((o.fontSize || 18) * PT)}px;`;
	if (o.color) s += `color:${rgba(o.color, o.transparency)};`;
	if (o.bold) s += "font-weight:700;";
	if (o.italic) s += "font-style:italic;";
	if (o.charSpacing) s += `letter-spacing:${n(o.charSpacing * PT)}px;`;
	if (font(o.fontFace)) s += `font-family:${font(o.fontFace)};`;
	const gap = o.paraSpaceAfter ? n(o.paraSpaceAfter * PT) : 0;
	const html = paragraphs(t).map((p, i, all) => {
		const runs = p.map((r) => {
			const ro = r.options;
			let rs = "";
			if (ro.color) rs += `color:${rgba(ro.color, ro.transparency)};`;
			if (ro.bold) rs += "font-weight:700;";
			if (ro.italic) rs += "font-style:italic;";
			if (ro.fontSize) rs += `font-size:${n(ro.fontSize * PT)}px;`;
			if (ro.charSpacing) rs += `letter-spacing:${n(ro.charSpacing * PT)}px;`;
			if (font(ro.fontFace)) rs += `font-family:${font(ro.fontFace)};`;
			const inner = esc(r.text);
			return ro.hyperlink
				? `<a href="${esc(ro.hyperlink.url)}" target="_blank" rel="noopener" style="${rs}">${inner}</a>`
				: rs ? `<span style="${rs}">${inner}</span>` : inner;
		}).join("");
		const bullet = p.some((r) => r.options.bullet);
		const ps = (i < all.length - 1 && gap ? `margin-bottom:${gap}px;` : "") + (bullet ? "padding-left:1.1em;text-indent:-1.1em;" : "");
		return `<p style="${ps}">${bullet ? "•&#8194;" : ""}${runs || "&#8203;"}</p>`;
	}).join("");
	return `<div ${attrs} class="el t" style="${css}${s}">${html}</div>`;
}

// ---------------------------------------------------------------- slides
const ACTOR = /^!!(glow|canvas|px\d|mark)$/; // shared shapes that glide between slides
const actorStates = {}; // name -> per-slide geometry
let actorMarkup = {}; // name -> element markup, from the first slide that has it
const textChars = new Set();

const sections = deck.slides.map((slide, si) => {
	const fx = new Map(ANIM[si].items.map((it) => [it.name, it]));
	const printActors = [];
	const body = slide.items.map((item) => {
		const o = item.o;
		const name = o.objectName || "";
		if (item.kind === "text") (typeof item.t === "string" ? [item.t] : item.t.map((r) => r.text)).forEach((s) => [...s].forEach((c) => textChars.add(c)));
		const anim = fx.get(name);
		const attrs = anim ? `data-fx="${anim.fx}"` : "";
		const css = anim ? `--at:${anim.at}ms;` : "";
		let html;
		if (item.kind === "text") html = renderText(item.t, o, attrs, css);
		else if (item.kind === "shape") html = renderShape(item.type, o, attrs, css);
		else html = `<div ${attrs} class="el img ${assetClass(o.path)}" style="${css}${box(o)}${o.rotate ? `transform:rotate(${o.rotate}deg);` : ""}"></div>`;
		const actor = ACTOR.exec(name);
		if (actor) {
			const key = actor[1];
			(actorStates[key] = actorStates[key] || [])[si] = {
				left: n(o.x * PX), top: n(o.y * PX), width: n(o.w * PX), height: n(o.h * PX), rotate: o.rotate || 0,
				color: o.fill ? rgba(o.fill.color, o.fill.transparency) : null,
			};
			if (!actorMarkup[key]) actorMarkup[key] = html.replace("<div ", `<div id="actor-${key}" `).replace("<svg ", `<svg id="actor-${key}" `);
			printActors.push(html);
			return "";
		}
		return html;
	}).join("");
	(slide.notes || "").split("").forEach((c) => textChars.add(c));
	return `<section class="slide" data-n="${si + 1}" aria-label="Slide ${si + 1}"><div class="print-actors">${printActors.join("")}</div>${body}</section>`;
});

// The mark turns the short way round between slides; unwrap its angles so CSS does too.
if (actorStates.mark) {
	let prev = 0;
	actorStates.mark.forEach((st, i) => {
		let d = (((st.rotate - prev) % 360) + 540) % 360 - 180;
		if (d === -180) d = 180;
		st.rotate = i === 0 ? st.rotate : prev + d;
		prev = st.rotate;
	});
}

// ---------------------------------------------------------------- fonts
function fontData() {
	const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "deckfont-"));
	const inter = path.join(ROOT, "static", "assets", "fonts", "Inter-Variable.ttf");
	const sub = path.join(tmp, "inter.woff2");
	const ui = " 0123456789/·•→←↑↓|?:.,—–'\"()+-%&";
	let interUrl;
	try {
		execFileSync("python3", ["-m", "fontTools.subset", inter, `--text=${[...textChars].join("")}${ui}`,
			"--unicodes=U+0020-007E,U+00A0-00FF,U+2010-2027,U+2190-2193", "--layout-features=*", "--flavor=woff2", `--output-file=${sub}`], { stdio: "pipe" });
		interUrl = `data:font/woff2;base64,${fs.readFileSync(sub).toString("base64")}`;
	} catch {
		interUrl = `data:font/ttf;base64,${fs.readFileSync(inter).toString("base64")}`; // no fontTools: embed it whole
	}
	const mono = require.resolve("@fontsource/jetbrains-mono/files/jetbrains-mono-latin-400-normal.woff2");
	return { interUrl, monoUrl: `data:font/woff2;base64,${fs.readFileSync(mono).toString("base64")}` };
}
const { interUrl, monoUrl } = fontData();
const assetCss = [...assets].map(([file, cls]) => `.${cls}{background-image:url(data:image/png;base64,${fs.readFileSync(file).toString("base64")})}`).join("\n");

// ---------------------------------------------------------------- page
const notes = deck.slides.map((s) => s.notes || "");
const W = 13.333 * PX, H = 7.5 * PX;
const actorOrder = ["glow", "canvas", ...Object.keys(actorMarkup).filter((k) => k.startsWith("px")).sort(), "mark"].filter((k) => actorMarkup[k]);

const page = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>4CE · Sovereign AI Workbench</title>
<style>
@font-face{font-family:'Inter';src:url(${interUrl});font-weight:100 900;font-style:normal;font-display:block}
@font-face{font-family:'JetBrains Mono';src:url(${monoUrl}) format('woff2');font-weight:400;font-display:block}
:root{--morph:${MORPH_MS}ms;--ease:cubic-bezier(.65,0,.35,1)}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:#0d0d0d;overflow:hidden}
body{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;-webkit-font-smoothing:antialiased;cursor:default}
body.idle{cursor:none}
#stage{position:absolute;left:50%;top:50%;width:${n(W)}px;height:${H}px;background:${rgba("tx1")};overflow:hidden;transform-origin:center}
.el{position:absolute;margin:0}
.t{display:flex;flex-direction:column;line-height:1.21;color:${rgba("bg1")}}
.t p{margin:0;white-space:pre-wrap}
.t a{color:inherit;text-decoration:underline;text-underline-offset:2px}
.img{background-size:100% 100%;background-repeat:no-repeat}
#actors .el{transition:left var(--morph) var(--ease),top var(--morph) var(--ease),width var(--morph) var(--ease),height var(--morph) var(--ease),transform var(--morph) var(--ease),color var(--morph) var(--ease),background-color var(--morph) var(--ease)}
.slide{position:absolute;inset:0;visibility:hidden;opacity:0;transition:opacity .35s ease,visibility 0s linear .35s}
.slide.active{visibility:visible;opacity:1;transition:opacity .8s ease .35s,visibility 0s}
.print-actors{display:none}
/* content builds in once the shared shapes have landed */
.slide [data-fx]{opacity:0}
.slide.play [data-fx]{animation-duration:.7s;animation-timing-function:cubic-bezier(.22,1,.36,1);animation-fill-mode:both;animation-delay:calc(var(--base,var(--morph)) + var(--at,0ms))}
.slide.play [data-fx=up]{animation-name:up}
.slide.play [data-fx=zoom]{animation-name:zoom;animation-duration:.5s}
.slide.play [data-fx=wipe]{animation-name:wipe;animation-duration:.5s;animation-timing-function:ease-out}
.slide.play [data-fx=fade]{animation-name:fade;animation-duration:.5s}
.slide.play [data-fx=fly]{animation-name:fly;animation-duration:1.2s;animation-timing-function:cubic-bezier(.34,1.4,.64,1)}
@keyframes up{from{opacity:0;translate:0 ${0.1 * H}px}to{opacity:1;translate:0 0}}
@keyframes zoom{from{opacity:0;scale:0}to{opacity:1;scale:1}}
@keyframes wipe{from{opacity:1;clip-path:inset(0 100% 0 0)}to{opacity:1;clip-path:inset(0 0 0 0)}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes fly{from{opacity:1;translate:0 ${0.45 * H}px}to{opacity:1;translate:0 0}}
/* no-motion mode: M key, ?static in the address, or the system's reduced-motion setting */
.still #actors .el,.still .slide,.still .slide.active{transition:none}
.still .slide [data-fx]{opacity:1;animation:none!important}
@media (prefers-reduced-motion:reduce){#actors .el,.slide,.slide.active{transition:none}.slide [data-fx]{opacity:1;animation:none!important}}
#hud{position:fixed;right:18px;bottom:14px;font:500 12px/1 'Inter',sans-serif;color:#9b9b9b;letter-spacing:.06em;opacity:0;transition:opacity .4s;pointer-events:none}
body.show-hud #hud{opacity:1}
#notes{position:fixed;left:0;right:0;bottom:0;max-height:34vh;overflow:auto;padding:18px 28px 22px;background:rgba(13,13,13,.94);border-top:1px solid #333;color:#eeeff1;font:15px/1.55 'Inter',sans-serif;display:none}
#notes b{color:#a78bfa;font-weight:600;letter-spacing:.08em;font-size:11px;display:block;margin-bottom:6px}
body.notes #notes{display:block}
#help{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);background:#262626;border:1px solid #333;border-radius:14px;padding:22px 26px;color:#eeeff1;font:14px/1.9 'Inter',sans-serif;display:none;min-width:320px}
#help kbd{font:12px 'JetBrains Mono',monospace;background:#171717;border:1px solid #333;border-radius:6px;padding:1px 7px;margin-right:8px;color:#a78bfa}
body.help #help{display:block}
@media print{
	@page{size:13.333in 7.5in;margin:0}
	html,body{overflow:visible;height:auto;background:none}
	#stage{position:static;transform:none!important;width:auto;height:auto;background:none;overflow:visible}
	#actors,#hud,#notes,#help{display:none!important}
	.slide{position:relative;visibility:visible;opacity:1;width:${n(W)}px;height:${H}px;overflow:hidden;background:${rgba("tx1")};break-after:page;zoom:.96;transition:none}
	.print-actors{display:block}
	.slide [data-fx]{opacity:1;animation:none!important}
}
${assetCss}
</style>
</head>
<body>
<div id="stage">
<div id="actors">${actorOrder.map((k) => actorMarkup[k]).join("")}</div>
${sections.join("\n")}
</div>
<div id="hud"></div>
<div id="notes"><b>SPEAKER NOTES</b><span></span></div>
<div id="help"><div><kbd>→</kbd><kbd>Space</kbd>next slide</div><div><kbd>←</kbd>previous slide</div><div><kbd>F</kbd>full screen</div><div><kbd>N</kbd>speaker notes</div><div><kbd>M</kbd>motion on / off</div><div><kbd>Home</kbd><kbd>End</kbd>first / last slide</div><div><kbd>?</kbd>this help</div></div>
<script>
const STATES = ${JSON.stringify(actorStates)};
const NOTES = ${JSON.stringify(notes)};
const stage = document.getElementById("stage");
const slides = [...document.querySelectorAll(".slide")];
const actors = Object.fromEntries(Object.keys(STATES).map((k) => [k, document.getElementById("actor-" + k)]));
let cur = -1;

function fit() {
	const s = Math.min(innerWidth / ${n(W)}, innerHeight / ${H});
	stage.style.transform = "translate(-50%,-50%) scale(" + s + ")";
}
function place(i) {
	for (const [k, el] of Object.entries(actors)) {
		const st = STATES[k][i];
		if (!el || !st) continue;
		Object.assign(el.style, { left: st.left + "px", top: st.top + "px", width: st.width + "px", height: st.height + "px", transform: "rotate(" + st.rotate + "deg)" });
		if (st.color) el.tagName === "svg" ? (el.style.color = st.color) : (el.style.backgroundColor = st.color);
	}
}
function go(i) {
	i = Math.max(0, Math.min(slides.length - 1, i));
	if (i === cur) return;
	const first = cur < 0;
	if (cur >= 0) slides[cur].classList.remove("active", "play");
	place(i);
	const s = slides[i];
	s.style.setProperty("--base", first ? "300ms" : "var(--morph)");
	s.classList.add("active");
	void s.offsetWidth; // restart the build-in animations
	s.classList.add("play");
	cur = i;
	history.replaceState(null, "", "#" + (i + 1));
	document.querySelector("#notes span").textContent = NOTES[i];
	hud();
}
let hudTimer;
function hud() {
	document.getElementById("hud").textContent = (cur + 1) + " / " + slides.length;
	document.body.classList.add("show-hud");
	clearTimeout(hudTimer);
	hudTimer = setTimeout(() => document.body.classList.remove("show-hud"), 1600);
}
addEventListener("keydown", (e) => {
	const k = e.key;
	if (["ArrowRight", "ArrowDown", "PageDown", " ", "Enter"].includes(k)) go(cur + 1);
	else if (["ArrowLeft", "ArrowUp", "PageUp", "Backspace"].includes(k)) go(cur - 1);
	else if (k === "Home") go(0);
	else if (k === "End") go(slides.length - 1);
	else if (k === "f" || k === "F") document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
	else if (k === "n" || k === "N") document.body.classList.toggle("notes");
	else if (k === "m" || k === "M") document.body.classList.toggle("still");
	else if (k === "?" || k === "h" || k === "H") document.body.classList.toggle("help");
	else if (k === "Escape") document.body.classList.remove("help", "notes");
	else return;
	e.preventDefault();
});
addEventListener("click", (e) => { if (!e.target.closest("a")) go(cur + (e.clientX < innerWidth / 4 ? -1 : 1)); });
let tx = null;
addEventListener("touchstart", (e) => { tx = e.touches[0].clientX; }, { passive: true });
addEventListener("touchend", (e) => { if (tx === null) return; const dx = e.changedTouches[0].clientX - tx; if (Math.abs(dx) > 40) go(cur + (dx < 0 ? 1 : -1)); tx = null; });
let idle;
addEventListener("mousemove", () => { document.body.classList.remove("idle"); clearTimeout(idle); idle = setTimeout(() => document.body.classList.add("idle"), 2000); });
addEventListener("resize", fit);
if (/[?&]static\\b/.test(location.search)) document.body.classList.add("still");
fit();
document.fonts.ready.then(() => go((parseInt(location.hash.slice(1), 10) || 1) - 1));
</script>
</body>
</html>
`;
fs.writeFileSync(OUT, page);
console.log("wrote", OUT, `(${Math.round(page.length / 1024)} KB)`);
