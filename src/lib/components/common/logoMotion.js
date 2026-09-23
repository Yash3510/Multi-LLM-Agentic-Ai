/*
 * The 4CE mark as moving parts, for LogoMotion.svelte (the avatar that shows
 * the agent chain at work) - the same split the opening intro uses
 * (static/4ce-intro.js).
 *
 * The traced artwork (4ce/branding/logo-mark.svg) is exactly a six-point star
 * core plus six cubes around an empty, cube-sized centre. Cubes sit at radius
 * D in the six hex directions; the three with a rhombus hole ("lit") have the
 * face towards the centre cut out. Clipping the artwork along that geometry
 * gives pieces that sum to the mark, so every motion moves the real logo and
 * nothing is redrawn.
 */

export const MARK = 'M138.66,0.00 134.79,1.44 102.08,20.38 99.61,22.88 98.79,26.13 98.88,60.88 98.14,63.63 96.91,64.90 94.54,65.89 91.79,65.03 61.39,47.38 58.04,46.79 55.29,47.38 20.66,67.43 18.54,69.81 17.85,72.01 17.83,111.76 18.41,115.01 21.16,117.93 51.57,135.38 53.16,136.94 53.62,139.26 53.17,141.51 51.91,142.93 21.41,160.47 18.48,163.38 17.80,166.88 17.83,206.38 19.39,210.01 22.04,211.96 54.91,230.96 58.04,231.87 61.91,230.91 91.91,213.40 94.41,212.84 96.52,213.38 98.14,214.88 98.83,217.51 98.80,252.38 99.66,255.82 103.29,258.93 136.49,278.01 139.41,278.71 144.04,277.02 177.16,257.81 179.04,255.79 179.91,252.26 179.85,217.63 180.64,214.76 182.19,213.38 184.16,212.80 186.79,213.39 216.79,230.90 220.66,231.87 223.91,230.89 258.16,211.04 260.16,208.76 260.88,206.38 260.91,166.76 260.26,163.51 257.29,160.47 226.79,142.92 225.54,141.60 225.07,139.13 225.60,136.76 227.15,135.38 257.41,118.00 260.16,115.26 260.85,112.63 260.85,72.01 260.16,69.83 258.03,67.38 223.41,47.37 220.66,46.80 217.29,47.38 186.91,65.02 184.29,65.89 181.79,64.92 180.39,63.26 179.84,60.63 179.90,26.01 179.04,22.72 176.41,20.28 143.91,1.43 141.66,0.30 138.66,0.00ZM138.66,93.49 136.04,94.44 101.53,114.38 99.59,116.51 98.91,119.88 98.89,154.88 99.22,160.88 101.41,164.03 135.66,183.91 139.54,185.12 143.04,183.91 177.29,164.02 179.12,161.88 179.78,158.38 179.78,120.01 179.16,116.66 177.16,114.38 142.55,94.38 138.66,93.49ZM139.04,46.88 136.54,47.37 106.77,64.51 104.41,66.38 103.57,67.76 103.40,69.38 103.76,70.88 105.63,73.01 136.66,90.91 139.66,91.38 142.04,90.91 173.04,73.04 174.93,70.88 175.29,69.38 175.13,67.76 174.29,66.38 171.90,64.51 142.16,47.38 139.04,46.88ZM62.41,142.62 59.54,144.17 58.38,146.88 58.36,182.51 59.43,185.88 61.66,187.95 92.68,205.88 95.91,205.85 98.13,203.88 98.91,201.63 98.85,166.38 98.16,163.50 96.42,161.38 65.79,143.50 62.41,142.62ZM215.41,142.62 213.04,143.48 182.31,161.38 180.54,163.43 179.83,166.01 179.85,201.63 180.64,204.01 182.91,205.85 185.16,206.05 187.41,205.03 216.94,188.01 219.29,185.81 220.33,182.51 220.30,146.76 219.41,144.51 218.40,143.51 215.41,142.62Z';

export const C = 139.355;
export const R = 46.82;
export const D = 92.54;
const RHB = 80.13; // star points: where neighbouring cubes pinch
const IN = D - R; // star notches: each cube's inner vertex
export const VIEW = 338.71; // the mark's 278.71 plus room to move

export const DIR = [-90, -30, 30, 90, 150, 210];
export const LIT = [true, false, true, false, true, false];

const u = (a) => [Math.cos((a * Math.PI) / 180), Math.sin((a * Math.PI) / 180)];
const at = (a, r) => [C + u(a)[0] * r, C + u(a)[1] * r];
const pts = (list) => list.map((p) => `${p[0].toFixed(2)},${p[1].toFixed(2)}`).join(' ');
const hexagon = (c) => [0, 1, 2, 3, 4, 5].map((j) => [c[0] + u(-90 + 60 * j)[0] * R, c[1] + u(-90 + 60 * j)[1] * R]);

export const CENTRES = DIR.map((a) => at(a, D));
const rings = MARK.split('Z')
	.filter((s) => s.trim())
	.map((s) => `${s.trim()}Z`);
export const OUTLINE = rings[0];
/* The open face of each lit cube, as drawn in the artwork. */
export const HOLES = { 0: rings[2], 2: rings[4], 4: rings[3] };

export const pieceClip = (k) =>
	pts([at(DIR[k] - 30, 700), at(DIR[k] - 30, RHB), at(DIR[k], IN), at(DIR[k] + 30, RHB), at(DIR[k] + 30, 700), at(DIR[k], 700)]);
export const hubClip = pts([...Array(12)].map((_, i) => at(-90 + 30 * i, i % 2 ? RHB : IN)));
export const hexPoints = (k) => pts(hexagon(CENTRES[k]));
export const axis = (k) => u(DIR[k]);

function bezier(x1, y1, x2, y2) {
	const f = (a, b, t) => 3 * a * t * (1 - t) * (1 - t) + 3 * b * t * t * (1 - t) + t * t * t;
	return (x) => {
		if (x <= 0) return 0;
		if (x >= 1) return 1;
		let lo = 0;
		let hi = 1;
		let t = x;
		for (let i = 0; i < 22; i++) {
			t = (lo + hi) / 2;
			if (f(x1, x2, t) < x) lo = t;
			else hi = t;
		}
		return f(y1, y2, t);
	};
}
export const SOFT = bezier(0.45, 0, 0.25, 1);
const OUT = bezier(0.22, 0.9, 0.3, 1);
const STD = bezier(0.4, 0, 0.2, 1);
const P = (t, a, b) => Math.min(1, Math.max(0, (t - a) / (b - a)));
const bell = (x) => (x <= 0 || x >= 1 ? 0 : Math.sin(Math.PI * x) ** 2);

/* A still frame: every piece where the artwork has it. */
export function rest() {
	return {
		cubes: [0, 1, 2, 3, 4, 5].map(() => ({ off: 0, rot: 0, orb: 0, sc: 1, face: 0, gap: null })),
		hub: 0,
		hubScale: 1,
		mark: 0,
		echo: 0,
		echoScale: 1
	};
}

/*
 * Each motion starts and ends on the exact mark. Rotations end on a symmetry
 * of what they turn - the whole mark or the ring of cubes by 120 degrees, a
 * cube by a full turn, the star core by 60 - so they land identical.
 */
export const MOTIONS = {
	// The ring of cubes turns a third round the core, one cube just behind the next.
	orbit: {
		period: 1900,
		at(t) {
			const s = rest();
			s.cubes.forEach((c, k) => {
				const q = P(t, 80 + k * 60, 1280 + k * 60);
				c.orb = 120 * SOFT(q);
				c.face = 0.8 * bell(q);
			});
			return s;
		}
	},
	// The cubes ease out along their lines and back, open-faced ones first.
	breathe: {
		period: 2500,
		at(t) {
			const s = rest();
			s.cubes.forEach((c, k) => {
				const d = LIT[k] ? 0 : 160;
				const a = SOFT(P(t, d, 800 + d)) - SOFT(P(t, 1150 + d, 2150 + d));
				c.off = 10 * a;
				c.face = 0.7 * a;
			});
			return s;
		}
	},
	// Each cube lifts in turn round the ring.
	wave: {
		period: 2700,
		at(t) {
			const s = rest();
			s.cubes.forEach((c, k) => {
				const b = bell(P(t, k * 230, k * 230 + 800));
				c.sc = 1 + 0.07 * b;
				c.off = 5 * b;
				c.face = b;
			});
			return s;
		}
	},
	// The cubes step out together and gather back onto the core.
	gather: {
		period: 3000,
		at(t) {
			const s = rest();
			const a = SOFT(P(t, 120, 1020)) - SOFT(P(t, 1550, 2650));
			s.cubes.forEach((c) => {
				c.off = 24 * a;
				c.face = a;
			});
			s.hubScale = 1 - 0.08 * a;
			return s;
		}
	},
	// TONY planning: the three axes nudge out in turn - three beats.
	triad: {
		period: 3300,
		at(t) {
			const s = rest();
			[[0, 3], [4, 1], [5, 2]].forEach((pair, i) => {
				const b = bell(P(t, i * 1050, i * 1050 + 1000));
				pair.forEach((k) => {
					s.cubes[k].off = 9 * b;
					s.cubes[k].face = 0.85 * b;
				});
			});
			return s;
		}
	},
	// FRIDAY analysing: a light passes round the ring.
	relay: {
		period: 2600,
		at(t) {
			const s = rest();
			s.cubes.forEach((c, k) => {
				const b = bell(P(t, k * 300, k * 300 + 900));
				c.face = b;
				c.off = 7 * b;
				c.sc = 1 + 0.05 * b;
			});
			return s;
		}
	},
	// JARVIS drafting: each cube turns once in place, like blocks being set.
	roll: {
		period: 3900,
		at(t) {
			const s = rest();
			s.cubes.forEach((c, k) => {
				const q = P(t, k * 400, k * 400 + 1500);
				c.rot = 360 * SOFT(q);
				c.face = bell(q);
				c.gap = 0;
			});
			return s;
		}
	},
	// A tool running: the star core turns a step while the cubes hold.
	hub: {
		period: 1500,
		at(t) {
			const s = rest();
			const q = P(t, 120, 1200);
			s.hub = 60 * SOFT(q);
			// The cubes step back while the core turns, so the turn shows
			// through the gaps instead of hiding behind them.
			s.cubes.forEach((c) => {
				c.off = 12 * bell(q);
				c.face = 0.6 * bell(q);
			});
			return s;
		}
	},
	// ULTRON checking: the whole mark turns a third, looking at every side.
	tumble: {
		period: 1900,
		at(t) {
			const s = rest();
			s.mark = 120 * SOFT(P(t, 120, 1500));
			return s;
		}
	},
	// TONY replanning: the open-faced cubes take turns sliding into the centre.
	slide: {
		period: 6000,
		at(t) {
			const s = rest();
			[0, 2, 4].forEach((k, i) => {
				const lt = t - i * 2000;
				const m = SOFT(P(lt, 150, 850)) - SOFT(P(lt, 1150, 1850));
				const c = s.cubes[k];
				c.off = -D * m;
				c.rot = 120 * m;
				c.face = Math.min(1, bell(P(lt, 0, 2000)) * 1.6);
			});
			return s;
		}
	},
	// Waiting for a person: a faint outline ripples out from a still mark.
	echo: {
		period: 2000,
		at(t) {
			const s = rest();
			const q = P(t, 0, 1750);
			s.echoScale = 1 + 0.32 * OUT(q);
			s.echo = q > 0 && q < 1 ? 0.85 * (1 - STD(q)) : 0;
			// The mark gives a small beat as each ripple leaves it.
			const beat = bell(P(t, 0, 520));
			s.cubes.forEach((c) => {
				c.off = 5 * beat;
				c.face = 0.5 * beat;
			});
			return s;
		}
	}
};

const nearest = (value, step) => Math.round(value / step) * step;
const mix = (a, b, w) => a + (b - a) * w;

/* `from` eased towards the still mark, w from 0 to 1. */
export function settle(from, w) {
	const to = rest();
	return {
		cubes: from.cubes.map((c) => ({
			off: mix(c.off, 0, w),
			rot: mix(c.rot, nearest(c.rot, 360), w),
			orb: mix(c.orb, nearest(c.orb, 120), w),
			sc: mix(c.sc, 1, w),
			face: mix(c.face, 0, w),
			gap: c.gap
		})),
		hub: mix(from.hub, nearest(from.hub, 60), w),
		hubScale: mix(from.hubScale, 1, w),
		mark: mix(from.mark, nearest(from.mark, 120), w),
		echo: mix(from.echo, to.echo, w),
		echoScale: from.echoScale
	};
}

export const isRest = (s) =>
	s.hub % 60 === 0 &&
	s.hubScale === 1 &&
	s.cubes.every(
		(c) =>
			Math.abs(c.off) < 0.01 &&
			Math.abs(c.rot % 360) < 0.01 &&
			Math.abs(c.orb % 120) < 0.01 &&
			Math.abs(c.sc - 1) < 0.001 &&
			c.face < 0.002
	);

/*
 * Every motion except the rejected "scan", in the order the avatar plays them
 * while the chain works - one loop each, calm and busier ones alternating.
 * Not tied to agents: the stage rail and the status line already say who is
 * working, so the mark is free to vary.
 */
export const ALL_MOTIONS = ['triad', 'relay', 'roll', 'orbit', 'breathe', 'hub', 'wave', 'tumble', 'gather', 'slide', 'echo'];

/* One animation frame loop shared by every animating mark on the page. */
const listeners = new Set();
let raf = 0;
function tick(now) {
	listeners.forEach((fn) => fn(now));
	raf = listeners.size ? requestAnimationFrame(tick) : 0;
}
export function onFrame(fn) {
	listeners.add(fn);
	if (!raf) raf = requestAnimationFrame(tick);
	return () => listeners.delete(fn);
}
