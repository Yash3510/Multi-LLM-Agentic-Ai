/*
 * 4CE opening intro. It plays right after signing in - the auth page calls
 * window.__fourceIntro.play() - and covers the switch into the chat. Hairline
 * construction lines draw in from their own sides, the star core traces and
 * fills, the six cubes dock along the lines and settle into the mark; then the
 * mark glides, upright and in a gentle arc, to the sidebar's own logo and
 * lands exactly on it as the app appears behind. With no sidebar logo on
 * screen (a narrow window), the cubes leave one pair at a time instead, in the
 * order they came, and the core fades last.
 *
 * Every piece on screen is the traced 4CE artwork (4ce/branding/logo-mark.svg)
 * clipped along its own geometry: a six-point star core plus six cubes around
 * an empty centre. Nothing is redrawn.
 *
 * A click or key press fast-forwards to the ending; reduced motion gets a
 * still mark and a fade.
 */
(function () {
	var root = document.documentElement;

	var MK = 'M138.66,0.00 134.79,1.44 102.08,20.38 99.61,22.88 98.79,26.13 98.88,60.88 98.14,63.63 96.91,64.90 94.54,65.89 91.79,65.03 61.39,47.38 58.04,46.79 55.29,47.38 20.66,67.43 18.54,69.81 17.85,72.01 17.83,111.76 18.41,115.01 21.16,117.93 51.57,135.38 53.16,136.94 53.62,139.26 53.17,141.51 51.91,142.93 21.41,160.47 18.48,163.38 17.80,166.88 17.83,206.38 19.39,210.01 22.04,211.96 54.91,230.96 58.04,231.87 61.91,230.91 91.91,213.40 94.41,212.84 96.52,213.38 98.14,214.88 98.83,217.51 98.80,252.38 99.66,255.82 103.29,258.93 136.49,278.01 139.41,278.71 144.04,277.02 177.16,257.81 179.04,255.79 179.91,252.26 179.85,217.63 180.64,214.76 182.19,213.38 184.16,212.80 186.79,213.39 216.79,230.90 220.66,231.87 223.91,230.89 258.16,211.04 260.16,208.76 260.88,206.38 260.91,166.76 260.26,163.51 257.29,160.47 226.79,142.92 225.54,141.60 225.07,139.13 225.60,136.76 227.15,135.38 257.41,118.00 260.16,115.26 260.85,112.63 260.85,72.01 260.16,69.83 258.03,67.38 223.41,47.37 220.66,46.80 217.29,47.38 186.91,65.02 184.29,65.89 181.79,64.92 180.39,63.26 179.84,60.63 179.90,26.01 179.04,22.72 176.41,20.28 143.91,1.43 141.66,0.30 138.66,0.00ZM138.66,93.49 136.04,94.44 101.53,114.38 99.59,116.51 98.91,119.88 98.89,154.88 99.22,160.88 101.41,164.03 135.66,183.91 139.54,185.12 143.04,183.91 177.29,164.02 179.12,161.88 179.78,158.38 179.78,120.01 179.16,116.66 177.16,114.38 142.55,94.38 138.66,93.49ZM139.04,46.88 136.54,47.37 106.77,64.51 104.41,66.38 103.57,67.76 103.40,69.38 103.76,70.88 105.63,73.01 136.66,90.91 139.66,91.38 142.04,90.91 173.04,73.04 174.93,70.88 175.29,69.38 175.13,67.76 174.29,66.38 171.90,64.51 142.16,47.38 139.04,46.88ZM62.41,142.62 59.54,144.17 58.38,146.88 58.36,182.51 59.43,185.88 61.66,187.95 92.68,205.88 95.91,205.85 98.13,203.88 98.91,201.63 98.85,166.38 98.16,163.50 96.42,161.38 65.79,143.50 62.41,142.62ZM215.41,142.62 213.04,143.48 182.31,161.38 180.54,163.43 179.83,166.01 179.85,201.63 180.64,204.01 182.91,205.85 185.16,206.05 187.41,205.03 216.94,188.01 219.29,185.81 220.33,182.51 220.30,146.76 219.41,144.51 218.40,143.51 215.41,142.62Z';
	var NS = 'http://www.w3.org/2000/svg';
	var C = 139.355, R = 46.82, D = 92.54, RHB = 80.13, IN = D - R;
	var DIR = [-90, -30, 30, 90, 150, 210], LIT = [1, 0, 1, 0, 1, 0];
	var DOCK = [1400, 1600, 1800, 1400, 1600, 1800];
	var HOLD = 3950, FLY0 = 3850, FLY1 = 5000;

	var playing = false;

	function play() {
		if (playing || root.classList.contains('her')) return;
		playing = true;
		var still = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
		var dark = root.classList.contains('dark');
		var oled = dark && root.style.getPropertyValue('--color-gray-900').trim() === '#000000';
		var BG = dark ? (oled ? '0,0,0' : '22,22,22') : '255,255,255';
		var INK = dark ? '#FFFFFF' : '#0D1117';
		var LINE = dark ? 'rgba(255,255,255,0.3)' : 'rgba(13,17,23,0.26)';
		var PAPER = 'rgb(' + BG + ')';
		var HAIR = Math.max(0.5, 1 / (window.devicePixelRatio || 1));

		function u(a) { return [Math.cos(a * Math.PI / 180), Math.sin(a * Math.PI / 180)]; }
		function at(a, r) { var v = u(a); return [C + v[0] * r, C + v[1] * r]; }
		function pts(a) { return a.map(function (p) { return p[0].toFixed(2) + ',' + p[1].toFixed(2); }).join(' '); }
		function hexp(c, r) { return [0, 1, 2, 3, 4, 5].map(function (j) { var v = u(-90 + 60 * j); return [c[0] + v[0] * r, c[1] + v[1] * r]; }); }
		function star12() { var a = []; for (var i = 0; i < 12; i++) a.push(at(-90 + 30 * i, i % 2 ? RHB : IN)); return a; }
		function el(tag, attrs, parent) {
			var e = document.createElementNS(NS, tag);
			for (var k in attrs) e.setAttribute(k, attrs[k]);
			if (parent) parent.appendChild(e);
			return e;
		}
		function bez(x1, y1, x2, y2) {
			function f(a, b, t) { return 3 * a * t * (1 - t) * (1 - t) + 3 * b * t * t * (1 - t) + t * t * t; }
			return function (x) {
				if (x <= 0) return 0;
				if (x >= 1) return 1;
				var lo = 0, hi = 1, t = x;
				for (var i = 0; i < 22; i++) { t = (lo + hi) / 2; if (f(x1, x2, t) < x) lo = t; else hi = t; }
				return f(y1, y2, t);
			};
		}
		var OUT = bez(0.22, 0.9, 0.3, 1), STD = bez(0.4, 0, 0.2, 1), SOFT = bez(0.45, 0, 0.25, 1), GLIDE = bez(0.5, 0, 0.15, 1);
		function P(t, a, b) { var x = (t - a) / (b - a); return x < 0 ? 0 : x > 1 ? 1 : x; }

		var ov = document.createElement('div');
		ov.id = 'fource-intro';
		ov.setAttribute('aria-hidden', 'true');
		ov.style.cssText = 'position:fixed;inset:0;z-index:2147483000;background:' + PAPER + ';';
		var svg = el('svg', { width: '100%', height: '100%' }, ov);
		svg.style.display = 'block';

		try {
			var subs = MK.split('Z').filter(function (s) { return s.trim(); }).map(function (s) { return s.trim() + 'Z'; });
			var HOLE = { 0: subs[2], 2: subs[4], 4: subs[3] };
			var CEN = DIR.map(function (a) { return at(a, D); });
			var defs = el('defs', {}, svg);
			el('path', { id: 'fi-mk', d: MK, 'fill-rule': 'evenodd' }, defs);
			el('path', { id: 'fi-ol', d: subs[0] }, defs);
			[0, 2, 4].forEach(function (k) { el('path', { id: 'fi-h' + k, d: HOLE[k] }, defs); });
			DIR.forEach(function (a, k) {
				var cp = el('clipPath', { id: 'fi-pk' + k }, defs);
				el('polygon', { points: pts([at(a - 30, 700), at(a - 30, RHB), at(a, IN), at(a + 30, RHB), at(a + 30, 700), at(a, 700)]) }, cp);
			});
			el('polygon', { points: pts(star12()) }, el('clipPath', { id: 'fi-hub' }, defs));

			var lg = el('g', {}, svg), fx = el('g', {}, svg), mg = el('g', {}, svg);
			var lines = [];
			[{ a: 90, t0: 0 }, { a: -30, t0: 230 }, { a: 210, t0: 460 }].forEach(function (b) {
				[-1, 1].forEach(function (sd, i) {
					lines.push({ a: b.a, sd: sd, t0: b.t0 + i * 90, e: el('line', { stroke: LINE, 'stroke-width': HAIR }, lg) });
				});
			});
			var ghosts = CEN.concat([[C, C]]).map(function (c) {
				return el('polygon', { points: pts(hexp(c, R)), fill: 'none', stroke: LINE, 'stroke-width': HAIR, 'stroke-dasharray': '4 4', 'vector-effect': 'non-scaling-stroke', opacity: 0 }, mg);
			});
			var seen = [];
			CEN.concat([[C, C]]).forEach(function (c) {
				hexp(c, R).forEach(function (p) {
					if (!seen.some(function (q) { return Math.hypot(q[0] - p[0], q[1] - p[1]) < 3; })) seen.push(p);
				});
			});
			var dots = seen.map(function (p) {
				return { d: Math.hypot(p[0] - C, p[1] - C), e: el('circle', { cx: p[0].toFixed(2), cy: p[1].toFixed(2), r: 0, fill: INK }, mg) };
			});
			var whole = el('use', { href: '#fi-mk', fill: INK }, mg);
			var star = el('polygon', { points: pts(star12()), fill: 'none', stroke: LINE, pathLength: 100, 'stroke-dasharray': '100 100', 'stroke-dashoffset': 100 }, mg);
			var hub = el('use', { href: '#fi-mk', fill: INK, 'clip-path': 'url(#fi-hub)' }, mg);
			var rip = el('use', { href: '#fi-ol', fill: 'none', stroke: LINE, opacity: 0 }, fx);
			var land = el('use', { href: '#fi-ol', fill: 'none', stroke: LINE, opacity: 0 }, fx);
			var cubes = [];
			[1, 3, 5, 0, 2, 4].forEach(function (k) {
				var c = CEN[k], g = el('g', {}, mg);
				var gap = el('polygon', { points: pts(hexp(c, R)), fill: 'none', stroke: PAPER, 'stroke-width': 4, 'stroke-linejoin': 'round', opacity: 0 }, g);
				el('use', { href: '#fi-mk', fill: INK, 'clip-path': 'url(#fi-pk' + k + ')' }, g);
				var fi, fs, o = (k + 3) % 6;
				if (LIT[k]) {
					fi = el('use', { href: '#fi-h' + k, fill: INK, opacity: 0 }, g);
					fs = el('use', { href: '#fi-h' + k, fill: PAPER, opacity: 0, transform: 'rotate(120 ' + c[0] + ' ' + c[1] + ')' }, g);
				} else {
					fi = el('use', { href: '#fi-h' + o, fill: PAPER, opacity: 0, transform: 'rotate(180 ' + C + ' ' + C + ')' }, g);
					fs = el('use', { href: '#fi-h' + o, fill: PAPER, opacity: 0, transform: 'rotate(120 ' + c[0] + ' ' + c[1] + ') rotate(180 ' + C + ' ' + C + ')' }, g);
				}
				cubes[k] = { g: g, fi: fi, fs: fs, gap: gap };
			});
		} catch (e) {
			playing = false;
			return;
		}

		document.body.appendChild(ov);

		var G = null;
		function measure() {
			var W = window.innerWidth, H = window.innerHeight;
			var s0 = Math.min(176, Math.max(120, H * 0.21)) / 278.71;
			svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
			star.setAttribute('stroke-width', HAIR / s0);
			lines.forEach(function (ln) {
				var v = u(ln.a), ax = v[0], ay = v[1], w = 40.55 * s0 * ln.sd;
				var mx = W / 2 - ay * w, my = H / 2 + ax * w, lo = -1e5, hi = 1e5;
				[[ax, mx, W], [ay, my, H]].forEach(function (q) {
					if (Math.abs(q[0]) > 1e-9) {
						var t1 = -q[1] / q[0], t2 = (q[2] - q[1]) / q[0];
						lo = Math.max(lo, Math.min(t1, t2));
						hi = Math.min(hi, Math.max(t1, t2));
					}
				});
				ln.x0 = mx + ax * lo; ln.y0 = my + ay * lo; ln.x1 = mx + ax * hi; ln.y1 = my + ay * hi;
			});
			G = { W: W, H: H, s0: s0 };
		}

		// The sidebar's logo, looked up once the app has had time to render under
		// the intro: undefined until then, null if none is showing. The collapsed
		// rail and the open sidebar each draw one, stacked in the same corner, so
		// every visible copy is held back until the mark lands.
		var target, marks = [];
		function findTarget() {
			var imgs = document.querySelectorAll('.sidebar-new-chat-icon img');
			for (var i = 0; i < imgs.length; i++) {
				var r = imgs[i].getBoundingClientRect();
				if (r.width > 4 && r.right > 0 && r.bottom > 0 && getComputedStyle(imgs[i]).display !== 'none') marks.push(imgs[i]);
			}
			return marks[0] || null;
		}
		function holdMarks(hidden) {
			marks.forEach(function (m) { m.style.visibility = hidden ? 'hidden' : ''; });
		}

		function render(t) {
			if (!G) measure();
			var W = G.W, H = G.H, s0 = G.s0;
			if (target === undefined && t >= FLY0 && !still) {
				target = findTarget();
				if (target) {
					holdMarks(true); // the mark flies in to take their place
					end = FLY1 + 750;
				}
			}
			var glide = !!target;
			var x = W / 2, y = H / 2, sc = s0, tr = null;
			if (glide) {
				tr = target.getBoundingClientRect();
				var tx = tr.left + tr.width / 2, ty = tr.top + tr.height / 2, ts = tr.width / 278.71;
				var e = GLIDE(P(t, FLY0, FLY1)), vx = tx - W / 2, vy = ty - H / 2;
				// A clear arc, not a straight line: it launches upward, then glides left.
				var qx = W / 2 + vx * 0.5 - vy * 0.17, qy = H / 2 + vy * 0.5 + vx * 0.17;
				x = (1 - e) * (1 - e) * (W / 2) + 2 * (1 - e) * e * qx + e * e * tx;
				y = (1 - e) * (1 - e) * (H / 2) + 2 * (1 - e) * e * qy + e * e * ty;
				sc = s0 + (ts - s0) * e;
				if (t >= FLY1) {
					mg.style.display = 'none';
					holdMarks(false);
				}
				var lp = P(t, FLY1, FLY1 + 750), lk = 1 + OUT(lp);
				land.setAttribute('transform', 'translate(' + tx + ' ' + ty + ') scale(' + ts * lk + ') translate(' + -C + ' ' + -C + ')');
				land.setAttribute('stroke-width', HAIR / (ts * lk));
				land.setAttribute('opacity', lp > 0 && lp < 1 ? 0.45 * (1 - STD(lp)) : 0);
			}
			mg.setAttribute('transform', 'translate(' + x + ' ' + y + ') scale(' + sc + ') translate(' + -C + ' ' + -C + ')');
			var bg = glide ? SOFT(P(t, FLY0 + 500, FLY1 + 150)) : SOFT(P(t, HOLD + 900, HOLD + 1800));
			ov.style.background = 'rgba(' + BG + ',' + (1 - bg) + ')';

			var p = P(t, 3300, 4200), k = 1 + 0.28 * OUT(p);
			rip.setAttribute('transform', 'translate(' + W / 2 + ' ' + H / 2 + ') scale(' + s0 * k + ') translate(' + -C + ' ' + -C + ')');
			rip.setAttribute('stroke-width', HAIR / (s0 * k));
			rip.setAttribute('opacity', !still && p > 0 && p < 1 ? 0.3 * (1 - STD(p)) : 0);

			var snap = SOFT(P(t, 3000, 3450)), leave = !glide && !still;
			var rest = t <= HOLD || glide;
			cubes.forEach(function (cb, k) {
				var q = P(t, DOCK[k], DOCK[k] + 1150), o = OUT(q), v = u(DIR[k]), c = CEN[k];
				// Leaving: pairs go in the order they docked, each easing out along
				// its own line as a solid cube again, then fading.
				var go = HOLD + 120 + ((DOCK[k] - DOCK[0]) / 200) * 220;
				var e = leave ? SOFT(P(t, go, go + 900)) : 0;
				var off = 260 * (1 - o) + 70 * e;
				var face = Math.max(1 - snap, leave ? 0.65 * SOFT(P(t, go, go + 260)) : 0);
				cb.g.setAttribute('transform', 'translate(' + (v[0] * off + c[0]) + ' ' + (v[1] * off + c[1]) + ') rotate(' + -120 * (1 - o) + ') scale(' + (1 + 0.18 * (1 - o)) + ') translate(' + -c[0] + ' ' + -c[1] + ')');
				cb.g.setAttribute('opacity', STD(P(q, 0, 0.22)) * (leave ? 1 - SOFT(P(t, go + 150, go + 900)) : 1));
				cb.fi.setAttribute('opacity', face * (LIT[k] ? 0.32 : 0.68));
				cb.fs.setAttribute('opacity', face * 0.16);
				cb.gap.setAttribute('opacity', face);
				if (q < 1 || face > 0.001) rest = false;
			});
			var sd = SOFT(P(t, 850, 1400));
			star.setAttribute('stroke-dashoffset', 100 - 100 * sd);
			star.setAttribute('opacity', sd > 0 ? 0.8 * (1 - STD(P(t, 1500, 1850))) : 0);
			var hq = P(t, 1250, 1700), ho = OUT(hq);
			var core = leave ? SOFT(P(t, HOLD + 700, HOLD + 1500)) : 0; // the core goes last
			hub.setAttribute('transform', 'translate(' + C + ' ' + C + ') scale(' + (0.86 + 0.14 * ho) * (1 - 0.06 * core) + ') translate(' + -C + ' ' + -C + ')');
			hub.setAttribute('opacity', STD(P(t, 1250, 1550)) * (1 - core));
			if (hq < 1) rest = false;
			whole.style.display = rest ? '' : 'none';
			hub.style.display = rest ? 'none' : '';
			cubes.forEach(function (cb) { cb.g.style.display = rest ? 'none' : ''; });

			var fade = 1 - SOFT(P(t, 3000, 3450));
			lines.forEach(function (ln) {
				var dd = OUT(P(t, ln.t0, ln.t0 + 1150)), oo = SOFT(P(t, 2950 + ln.t0 * 0.4, 3700 + ln.t0 * 0.4));
				ln.e.setAttribute('x1', ln.x0 + (ln.x1 - ln.x0) * oo);
				ln.e.setAttribute('y1', ln.y0 + (ln.y1 - ln.y0) * oo);
				ln.e.setAttribute('x2', ln.x0 + (ln.x1 - ln.x0) * dd);
				ln.e.setAttribute('y2', ln.y0 + (ln.y1 - ln.y0) * dd);
				ln.e.setAttribute('opacity', dd > 0 && oo < 1 ? 1 : 0);
			});
			var gb = 0.45 * STD(P(t, 650, 1100)) * fade;
			ghosts.forEach(function (gh) { gh.setAttribute('opacity', gb); });
			dots.forEach(function (dt) {
				dt.e.setAttribute('r', (1.8 * OUT(P(t, 700 + 2 * dt.d, 1100 + 2 * dt.d)) * fade).toFixed(2));
			});
			ov.style.pointerEvents = t > (glide ? FLY0 + 500 : HOLD + 900) ? 'none' : '';
		}

		var T = still ? HOLD : 0, end = HOLD + 1850, drawn = -1, last = 0, rush = false, raf = 0;
		function finish() {
			cancelAnimationFrame(raf);
			holdMarks(false);
			window.removeEventListener('resize', onResize);
			window.removeEventListener('keydown', onSkip, true);
			ov.removeEventListener('pointerdown', onSkip);
			ov.remove();
			playing = false;
		}
		function frame(now) {
			// Capped so a long stall while the app boots slows the intro instead of
			// making it jump.
			var dt = last ? Math.min(100, now - last) : 0;
			last = now;
			if (T < HOLD) T = Math.min(HOLD, T + dt * (rush ? 6 : 1));
			else T += dt;
			if (T >= end) return finish();
			if (T !== drawn) render((drawn = T));
			raf = requestAnimationFrame(frame);
		}
		function onSkip() { rush = true; }
		function onResize() { G = null; render(T); }
		window.addEventListener('resize', onResize);
		window.addEventListener('keydown', onSkip, true);
		ov.addEventListener('pointerdown', onSkip);
		render((drawn = T));
		raf = requestAnimationFrame(frame);
	}

	window.__fourceIntro = { play: play };
})();
