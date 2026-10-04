// Renders the picture assets the deck uses: the four-pillar wheel, the glow orbs that drift
// between slides, and every icon (as PNG, so PowerPoint never needs the icon font).
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
	navy: "#011936",
	blue: "#1D74FF",
	mint: "#1BDD96",
	cyan: "#00B0F0",
	sky: "#6AC4E6",
	white: "#FFFFFF",
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
	const tones = { navy: COLORS.navy, blue: COLORS.blue, mint: COLORS.mint, white: COLORS.white, sky: COLORS.sky };
	for (const [name, Comp] of Object.entries(ICONS)) {
		for (const [tone, color] of Object.entries(tones)) {
			const svg = iconSvg(Comp, color, 256).replace(/currentColor/g, color);
			await sharp(Buffer.from(svg)).resize(256, 256).png().toFile(path.join(OUT, `icon-${name}-${tone}.png`));
		}
	}
}

// ---------- glow orbs ----------
async function renderOrb(name, color, peak) {
	const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800">
	<defs><radialGradient id="g" cx="50%" cy="50%" r="50%">
		<stop offset="0%" stop-color="${color}" stop-opacity="${peak}"/>
		<stop offset="35%" stop-color="${color}" stop-opacity="${peak * 0.45}"/>
		<stop offset="70%" stop-color="${color}" stop-opacity="${peak * 0.12}"/>
		<stop offset="100%" stop-color="${color}" stop-opacity="0"/>
	</radialGradient></defs>
	<circle cx="400" cy="400" r="400" fill="url(#g)"/></svg>`;
	await sharp(Buffer.from(svg)).png().toFile(path.join(OUT, `orb-${name}.png`));
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
		body += `<path d="${d}" fill="url(#seg)" filter="url(#sh)"/>`;

		// icon on the segment's centre line
		const ic = iconInner(s.icon, COLORS.blue);
		const [ix, iy] = pt(330, s.mid);
		const isz = 150;
		body += `<svg x="${ix - isz / 2}" y="${iy - isz / 2}" width="${isz}" height="${isz}" viewBox="${ic.viewBox}"><g ${ic.g.replace(/currentColor/g, COLORS.blue)}>${ic.inner.replace(/currentColor/g, COLORS.blue)}</g></svg>`;

		// label set along the rim, rotated tangentially
		const [lx, ly] = pt(475, s.mid);
		let rot = s.mid + 90;
		if (s.mid === 90) rot = 0; // bottom label reads upright
		body += `<text x="${lx}" y="${ly}" transform="rotate(${rot} ${lx} ${ly})" text-anchor="middle" dominant-baseline="central" font-family="Liberation Sans, Arial, sans-serif" font-weight="700" font-size="50" letter-spacing="6" fill="${COLORS.navy}">${s.label}</text>`;
	});

	const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${S}" height="${S}" viewBox="0 0 ${S} ${S}">
	<defs>
		<radialGradient id="seg" cx="50%" cy="50%" r="50%">
			<stop offset="0%" stop-color="#DCE8FB"/>
			<stop offset="45%" stop-color="#F4F8FF"/>
			<stop offset="100%" stop-color="#FFFFFF"/>
		</radialGradient>
		<filter id="sh" x="-20%" y="-20%" width="140%" height="140%">
			<feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#011936" flood-opacity="0.35"/>
		</filter>
	</defs>
	${body}
	<circle cx="${c}" cy="${c}" r="${rIn - 22}" fill="${COLORS.navy}"/>
	<circle cx="${c}" cy="${c}" r="${rIn - 52}" fill="none" stroke="${COLORS.mint}" stroke-width="14"/>
	<circle cx="${c}" cy="${c}" r="26" fill="${COLORS.mint}"/>
</svg>`;
	fs.writeFileSync(path.join(OUT, "wheel.svg"), svg);
	await sharp(Buffer.from(svg)).png().toFile(path.join(OUT, "wheel.png"));
}

(async () => {
	await renderWheel();
	await renderOrb("mint", COLORS.mint, 0.55);
	await renderOrb("cyan", COLORS.cyan, 0.5);
	await renderOrb("blue", COLORS.blue, 0.6);
	await renderIcons();
	console.log("assets written to", OUT);
})();
