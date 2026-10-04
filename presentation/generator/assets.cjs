// Renders the picture assets the deck uses: the four-pillar wheel and every icon (as PNG, so
// PowerPoint never needs the icon font).
const fs = require("fs");
const path = require("path");
const sharp = require("sharp");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const lu = require("react-icons/lu");
const fa = require("react-icons/fa6");

const OUT = path.join(__dirname, "assets");
fs.mkdirSync(OUT, { recursive: true });

const COLORS = {
	black: "#141414",
	bone: "#F2F2EE",
	orange: "#FF5B1A",
};

// ---------- icons ----------
const ICONS = {
	shield: lu.LuShieldCheck,
	fileIn: lu.LuFileInput,
	userCheck: lu.LuUserCheck,
	badge: lu.LuBadgeCheck,
	box: lu.LuBox,
	sliders: lu.LuSlidersHorizontal,
	cpu: lu.LuCpu,
	code: lu.LuCode,
	server: lu.LuServer,
	brain: lu.LuBrain,
	database: lu.LuDatabase,
	container: lu.LuContainer,
	fileText: lu.LuFileText,
	wrench: lu.LuWrench,
	arrow: lu.LuArrowRight,
	hardDrive: lu.LuHardDrive,
	layers: lu.LuLayers,
	trendDown: lu.LuTrendingDown,
	briefcase: lu.LuBriefcase,
	repeat: lu.LuRepeat,
	chat: lu.LuMessagesSquare,
	flask: lu.LuFlaskConical,
	landmark: lu.LuLandmark,
	network: lu.LuNetwork,
	factory: lu.LuFactory,
	eye: lu.LuScanEye,
	building: lu.LuBuilding2,
	bot: lu.LuBot,
	book: lu.LuBookOpen,
	fileCode: lu.LuFileCode,
	chart: lu.LuChartBar,
	link: lu.LuLink,
	play: lu.LuCirclePlay,
	lock: lu.LuLock,
	github: fa.FaGithub,
	docker: fa.FaDocker,
};

function iconSvg(Comp, color, size) {
	return ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color, size: String(size) }));
}

// Inner <svg> markup of an icon, for embedding inside a larger SVG.
function iconInner(Comp, color) {
	const svg = iconSvg(Comp, color, 24);
	const viewBox = /viewBox="([^"]+)"/.exec(svg)[1];
	const inner = svg.replace(/^<svg[^>]*>/, "").replace(/<\/svg>$/, "");
	const attrs = /^<svg([^>]*)>/.exec(svg)[1];
	const stroke = /stroke="([^"]+)"/.exec(attrs);
	const fill = /fill="([^"]+)"/.exec(attrs);
	const sw = /stroke-width="([^"]+)"/.exec(attrs);
	const lc = /stroke-linecap="([^"]+)"/.exec(attrs);
	const lj = /stroke-linejoin="([^"]+)"/.exec(attrs);
	const g = [
		stroke ? `stroke="${stroke[1]}"` : "",
		fill ? `fill="${fill[1]}"` : "",
		sw ? `stroke-width="${sw[1]}"` : "",
		lc ? `stroke-linecap="${lc[1]}"` : "",
		lj ? `stroke-linejoin="${lj[1]}"` : "",
	].join(" ");
	return { viewBox, inner, g };
}

async function renderIcons() {
	const tones = COLORS;
	for (const [name, Comp] of Object.entries(ICONS)) {
		for (const [tone, color] of Object.entries(tones)) {
			const svg = iconSvg(Comp, color, 256).replace(/currentColor/g, color);
			await sharp(Buffer.from(svg)).resize(256, 256).png().toFile(path.join(OUT, `icon-${name}-${tone}.png`));
		}
	}
}

// ---------- the four-pillar wheel ----------
// One picture whose canvas is the whole wheel, so turning the picture turns the wheel
// about its own centre - Morph then spins it between slides.
async function renderWheel() {
	const S = 1200, c = S / 2;
	const rOut = 560, rIn = 150, gap = 3.2; // gap in degrees between segments
	const segs = [
		{ label: "SOVEREIGNTY", icon: ICONS.shield, mid: -90 },
		{ label: "INGESTION", icon: ICONS.fileIn, mid: 0 },
		{ label: "GOVERNANCE", icon: ICONS.userCheck, mid: 90 },
		{ label: "TRUST", icon: ICONS.badge, mid: 180 },
	];
	const rad = (d) => (d * Math.PI) / 180;
	const pt = (r, d) => [c + r * Math.cos(rad(d)), c + r * Math.sin(rad(d))];

	let body = "";
	segs.forEach((s, i) => {
		const a0 = s.mid - 45 + gap / 2, a1 = s.mid + 45 - gap / 2;
		const [x0, y0] = pt(rOut, a0), [x1, y1] = pt(rOut, a1);
		const [x2, y2] = pt(rIn, a1), [x3, y3] = pt(rIn, a0);
		const d = `M${x0},${y0} A${rOut},${rOut} 0 0 1 ${x1},${y1} L${x2},${y2} A${rIn},${rIn} 0 0 0 ${x3},${y3} Z`;
		body += `<path d="${d}" fill="${COLORS.bone}"/>`;

		// icon on the segment's centre line
		const ic = iconInner(s.icon, COLORS.black);
		const [ix, iy] = pt(330, s.mid);
		const isz = 150;
		body += `<svg x="${ix - isz / 2}" y="${iy - isz / 2}" width="${isz}" height="${isz}" viewBox="${ic.viewBox}"><g ${ic.g.replace(/currentColor/g, COLORS.black)}>${ic.inner.replace(/currentColor/g, COLORS.black)}</g></svg>`;

		// label set along the rim, rotated tangentially
		const [lx, ly] = pt(475, s.mid);
		let rot = s.mid + 90;
		if (s.mid === 90) rot = 0; // bottom label reads upright
		body += `<text x="${lx}" y="${ly}" transform="rotate(${rot} ${lx} ${ly})" text-anchor="middle" dominant-baseline="central" font-family="Inter, Liberation Sans, sans-serif" font-weight="700" font-size="50" letter-spacing="6" fill="${COLORS.black}">${s.label}</text>`;
	});

	const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${S}" height="${S}" viewBox="0 0 ${S} ${S}">
	${body}
	<circle cx="${c}" cy="${c}" r="${rIn - 22}" fill="${COLORS.black}"/>
	<circle cx="${c}" cy="${c}" r="${rIn - 56}" fill="none" stroke="${COLORS.orange}" stroke-width="10"/>
	<circle cx="${c}" cy="${c}" r="24" fill="${COLORS.orange}"/>
</svg>`;
	fs.writeFileSync(path.join(OUT, "wheel.svg"), svg);
	await sharp(Buffer.from(svg)).png().toFile(path.join(OUT, "wheel.png"));
}

(async () => {
	await renderWheel();
	await renderIcons();
	console.log("assets written to", OUT);
})();
