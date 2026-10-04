// Renders the picture assets the deck uses, all in the 4CE chat UI's palette: every icon (as
// PNG, so PowerPoint never needs the icon font), the violet corner glow of the dark scenes, the
// pixel-block wave, and logo.json - the 4CE mark as polygon points for a native vector shape.
const fs = require("fs");
const path = require("path");
const sharp = require("sharp");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const lu = require("react-icons/lu");
const fa = require("react-icons/fa6");

const OUT = path.join(__dirname, "assets");
fs.mkdirSync(OUT, { recursive: true });

// 4CE chat UI: page #171717, light canvas #EEEFF1, violet-600/400, emerald-400, amber-400
const COLORS = {
	dark: "#171717",
	light: "#EEEFF1",
	muted: "#9B9B9B",
	violet: "#7C3AED",
	lilac: "#A78BFA",
	green: "#34D399",
	amber: "#FBBF24",
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
	wrench: lu.LuWrench,
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
	fileText: lu.LuFileText,
	chart: lu.LuChartBar,
	play: lu.LuCirclePlay,
	lock: lu.LuLock,
	plus: lu.LuPlus,
	mic: lu.LuMic,
	arrowUp: lu.LuArrowUp,
	chevron: lu.LuChevronDown,
	check: lu.LuCheck,
	download: lu.LuDownload,
	external: lu.LuExternalLink,
	sparkle: lu.LuSparkles,
	github: fa.FaGithub,
	docker: fa.FaDocker,
};

function iconSvg(Comp, color, size) {
	return ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color, size: String(size) }));
}

async function renderIcons() {
	for (const [name, Comp] of Object.entries(ICONS)) {
		for (const [tone, color] of Object.entries(COLORS)) {
			const svg = iconSvg(Comp, color, 256).replace(/currentColor/g, color);
			await sharp(Buffer.from(svg)).resize(256, 256).png().toFile(path.join(OUT, `icon-${name}-${tone}.png`));
		}
	}
}

// ---------- violet corner glow (the dark scenes in the demo) ----------
async function renderGlow() {
	const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800">
	<defs><radialGradient id="g" cx="50%" cy="50%" r="50%">
		<stop offset="0%" stop-color="${COLORS.violet}" stop-opacity="0.30"/>
		<stop offset="45%" stop-color="${COLORS.violet}" stop-opacity="0.12"/>
		<stop offset="100%" stop-color="${COLORS.violet}" stop-opacity="0"/>
	</radialGradient></defs>
	<circle cx="400" cy="400" r="400" fill="url(#g)"/></svg>`;
	await sharp(Buffer.from(svg)).png().toFile(path.join(OUT, "glow.png"));
}

// ---------- pixel-block wave (the "Nothing leaves the building" band) ----------
// Columns of stacked violet squares, darkest next to the band, fading outwards.
async function renderWave() {
	const cols = 96, cell = 20, rows = 5, W = cols * cell, H = rows * cell;
	const tiers = ["#5836A6", "#6B45BC", "#7C57C8", "#9C7FD9", "#C9B8F0"];
	let rects = "";
	for (let c = 0; c < cols; c++) {
		// two slow waves give the stepped silhouette its rhythm
		const h = 1.6 + 1.6 * Math.sin(c / 7.5) + 1.2 * Math.sin(c / 3.1 + 1.3);
		const n = Math.max(1, Math.min(rows, Math.round(h)));
		for (let r = 0; r < n; r++) {
			rects += `<rect x="${c * cell}" y="${H - (r + 1) * cell}" width="${cell}" height="${cell}" fill="${tiers[r]}"/>`;
		}
	}
	const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${rects}</svg>`;
	await sharp(Buffer.from(svg)).png().toFile(path.join(OUT, "wave.png"));
	await sharp(Buffer.from(svg)).flip().png().toFile(path.join(OUT, "wave-down.png")); // for the band's lower edge
}

// ---------- the 4CE mark as polygon rings, from 4ce/branding/logo-mark.svg ----------
function logoRings() {
	const svg = fs.readFileSync(path.join(__dirname, "..", "..", "4ce", "branding", "logo-mark.svg"), "utf8");
	const size = Number(/viewBox="0 0 ([\d.]+)/.exec(svg)[1]);
	const d = /\bd="([^"]+)"/.exec(svg)[1];
	return d.split("Z").map((s) => s.replace("M", "").trim()).filter(Boolean).map((ring) =>
		ring.split(/\s+/).map((pair) => pair.split(",").map((v) => Number(v) / size)));
}

(async () => {
	fs.writeFileSync(path.join(OUT, "logo.json"), JSON.stringify(logoRings()));
	await renderGlow();
	await renderWave();
	await renderIcons();
	console.log("assets written to", OUT);
})();
