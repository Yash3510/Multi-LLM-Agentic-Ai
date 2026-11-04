/*
 * The 4CE sign-in intro (entry look E4), brought over from the owner's own 4ce-intro.js with its
 * timeline unchanged. It plays right after signing in and covers the switch into the app.
 * Hairline construction lines draw in from their own sides, the star core traces and fills, and
 * the six cubes dock along the lines and settle into the mark. Then the mark glides, upright and
 * in a gentle arc, to the sidebar's own logo and lands exactly on it as the app appears behind.
 * Where only a button stands for the folded sidebar ([data-intro-dock]), it takes the same arc
 * into that button. With neither on screen, the cubes leave one pair at a time and the core fades
 * last.
 *
 * Every piece on screen is the brand-kit mark clipped along its own geometry: a six-point star
 * core plus six cubes around an empty centre. Nothing is redrawn.
 *
 * A click or key press fast-forwards to the ending; reduced motion gets a still mark and a fade.
 */
import brand from '$lib/ui/brand/4ce-logomark-ink.svg?raw';

type Point = [number, number];
type Attrs = Record<string, string | number>;

const MK = /\sd="([^"]+)"/.exec(brand)?.[1] ?? '';
const NS = 'http://www.w3.org/2000/svg';
const C = 139.355;
const R = 46.82;
const D = 92.54;
const RHB = 80.13;
const IN = D - R;
const DIR = [-90, -30, 30, 90, 150, 210];
const LIT = [1, 0, 1, 0, 1, 0];
const DOCK = [1400, 1600, 1800, 1400, 1600, 1800];
const HOLD = 3950;
const FLY0 = 3850;
const FLY1 = 5000;

let playing = false;

/** "r,g,b" from a token's computed value, in whatever form it was written (a minifier may
 * shorten or name it): the browser computes it to rgb(). */
function channels(value: string): string {
  const probe = document.body.appendChild(document.createElement('i'));
  probe.style.color = value;
  const rgb = /^rgba?\((\d+),\s*(\d+),\s*(\d+)/.exec(getComputedStyle(probe).color);
  probe.remove();
  if (!value || !rgb) throw new Error(`intro: cannot read colour ${value}`);
  return rgb.slice(1).join(',');
}

function unit(a: number): Point {
  return [Math.cos((a * Math.PI) / 180), Math.sin((a * Math.PI) / 180)];
}
function at(a: number, r: number): Point {
  const v = unit(a);
  return [C + v[0] * r, C + v[1] * r];
}
function pts(list: Point[]) {
  return list.map((p) => p[0].toFixed(2) + ',' + p[1].toFixed(2)).join(' ');
}
function hexp(c: Point, r: number): Point[] {
  return [0, 1, 2, 3, 4, 5].map((j) => {
    const v = unit(-90 + 60 * j);
    return [c[0] + v[0] * r, c[1] + v[1] * r];
  });
}
function star12() {
  const list: Point[] = [];
  for (let i = 0; i < 12; i++) list.push(at(-90 + 30 * i, i % 2 ? RHB : IN));
  return list;
}
function el(tag: string, attrs: Attrs, parent?: Element): SVGElement {
  const e = document.createElementNS(NS, tag) as SVGElement;
  for (const k in attrs) e.setAttribute(k, String(attrs[k]));
  if (parent) parent.appendChild(e);
  return e;
}
function bez(x1: number, y1: number, x2: number, y2: number) {
  const f = (a: number, b: number, t: number) =>
    3 * a * t * (1 - t) * (1 - t) + 3 * b * t * t * (1 - t) + t * t * t;
  return (x: number) => {
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
const OUT = bez(0.22, 0.9, 0.3, 1);
const STD = bez(0.4, 0, 0.2, 1);
const SOFT = bez(0.45, 0, 0.25, 1);
const GLIDE = bez(0.5, 0, 0.15, 1);
function P(t: number, a: number, b: number) {
  const x = (t - a) / (b - a);
  return x < 0 ? 0 : x > 1 ? 1 : x;
}

function shown(node: Element) {
  const r = node.getBoundingClientRect();
  return r.width > 4 && r.right > 0 && r.bottom > 0 && getComputedStyle(node).display !== 'none';
}

export function playIntro() {
  if (playing) return;
  playing = true;
  const root = document.documentElement;
  const still = root.dataset.motion === 'reduce';
  const dark = root.dataset.theme === 'dark';
  const tokens = getComputedStyle(root);
  let BG: string;
  let INK: string;
  try {
    BG = channels(tokens.getPropertyValue('--color-intro-ground').trim());
    INK = 'rgb(' + channels(tokens.getPropertyValue('--color-intro-ink').trim()) + ')';
  } catch {
    playing = false;
    return;
  }
  const LINE = 'rgba(' + INK.slice(4, -1) + ',' + (dark ? 0.3 : 0.26) + ')';
  const PAPER = 'rgb(' + BG + ')';
  const HAIR = Math.max(0.5, 1 / (window.devicePixelRatio || 1));

  const ov = document.createElement('div');
  ov.id = 'fource-intro';
  ov.setAttribute('aria-hidden', 'true');
  ov.style.cssText = 'position:fixed;inset:0;z-index:2147483000;background:' + PAPER + ';';
  const svg = el('svg', { width: '100%', height: '100%' }, ov);
  svg.style.display = 'block';

  const subs = MK.split('Z')
    .filter((s) => s.trim())
    .map((s) => s.trim() + 'Z');
  const HOLE: Record<number, string> = { 0: subs[2], 2: subs[4], 4: subs[3] };
  const CEN = DIR.map((a) => at(a, D));
  const defs = el('defs', {}, svg);
  el('path', { id: 'fi-mk', d: MK, 'fill-rule': 'evenodd' }, defs);
  el('path', { id: 'fi-ol', d: subs[0] }, defs);
  [0, 2, 4].forEach((k) => el('path', { id: 'fi-h' + k, d: HOLE[k] }, defs));
  DIR.forEach((a, k) => {
    const cp = el('clipPath', { id: 'fi-pk' + k }, defs);
    el(
      'polygon',
      {
        points: pts([
          at(a - 30, 700),
          at(a - 30, RHB),
          at(a, IN),
          at(a + 30, RHB),
          at(a + 30, 700),
          at(a, 700),
        ]),
      },
      cp,
    );
  });
  el('polygon', { points: pts(star12()) }, el('clipPath', { id: 'fi-hub' }, defs));

  const lg = el('g', {}, svg);
  const fx = el('g', {}, svg);
  const mg = el('g', {}, svg);
  type Line = {
    a: number;
    sd: number;
    t0: number;
    e: SVGElement;
    x0: number;
    y0: number;
    x1: number;
    y1: number;
  };
  const lines: Line[] = [];
  [
    { a: 90, t0: 0 },
    { a: -30, t0: 230 },
    { a: 210, t0: 460 },
  ].forEach((b) => {
    [-1, 1].forEach((sd, i) => {
      const e = el('line', { stroke: LINE, 'stroke-width': HAIR }, lg);
      lines.push({ a: b.a, sd, t0: b.t0 + i * 90, e, x0: 0, y0: 0, x1: 0, y1: 0 });
    });
  });
  const ghosts = CEN.concat([[C, C]]).map((c) =>
    el(
      'polygon',
      {
        points: pts(hexp(c, R)),
        fill: 'none',
        stroke: LINE,
        'stroke-width': HAIR,
        'stroke-dasharray': '4 4',
        'vector-effect': 'non-scaling-stroke',
        opacity: 0,
      },
      mg,
    ),
  );
  const seen: Point[] = [];
  CEN.concat([[C, C]]).forEach((c) => {
    hexp(c, R).forEach((p) => {
      if (!seen.some((q) => Math.hypot(q[0] - p[0], q[1] - p[1]) < 3)) seen.push(p);
    });
  });
  const dots = seen.map((p) => ({
    d: Math.hypot(p[0] - C, p[1] - C),
    e: el('circle', { cx: p[0].toFixed(2), cy: p[1].toFixed(2), r: 0, fill: INK }, mg),
  }));
  const whole = el('use', { href: '#fi-mk', fill: INK }, mg);
  const star = el(
    'polygon',
    {
      points: pts(star12()),
      fill: 'none',
      stroke: LINE,
      pathLength: 100,
      'stroke-dasharray': '100 100',
      'stroke-dashoffset': 100,
    },
    mg,
  );
  const hub = el('use', { href: '#fi-mk', fill: INK, 'clip-path': 'url(#fi-hub)' }, mg);
  const rip = el('use', { href: '#fi-ol', fill: 'none', stroke: LINE, opacity: 0 }, fx);
  const land = el('use', { href: '#fi-ol', fill: 'none', stroke: LINE, opacity: 0 }, fx);
  type Cube = { g: SVGElement; fi: SVGElement; fs: SVGElement; gap: SVGElement };
  const cubes: Cube[] = [];
  [1, 3, 5, 0, 2, 4].forEach((k) => {
    const c = CEN[k];
    const g = el('g', {}, mg);
    const gap = el(
      'polygon',
      {
        points: pts(hexp(c, R)),
        fill: 'none',
        stroke: PAPER,
        'stroke-width': 4,
        'stroke-linejoin': 'round',
        opacity: 0,
      },
      g,
    );
    el('use', { href: '#fi-mk', fill: INK, 'clip-path': 'url(#fi-pk' + k + ')' }, g);
    const o = (k + 3) % 6;
    let fi: SVGElement;
    let fs: SVGElement;
    if (LIT[k]) {
      fi = el('use', { href: '#fi-h' + k, fill: INK, opacity: 0 }, g);
      fs = el(
        'use',
        { href: '#fi-h' + k, fill: PAPER, opacity: 0, transform: `rotate(120 ${c[0]} ${c[1]})` },
        g,
      );
    } else {
      fi = el(
        'use',
        { href: '#fi-h' + o, fill: PAPER, opacity: 0, transform: `rotate(180 ${C} ${C})` },
        g,
      );
      fs = el(
        'use',
        {
          href: '#fi-h' + o,
          fill: PAPER,
          opacity: 0,
          transform: `rotate(120 ${c[0]} ${c[1]}) rotate(180 ${C} ${C})`,
        },
        g,
      );
    }
    cubes[k] = { g, fi, fs, gap };
  });

  document.body.appendChild(ov);

  let G: { W: number; H: number; s0: number } | null = null;
  function measure() {
    const W = window.innerWidth;
    const H = window.innerHeight;
    const s0 = Math.min(176, Math.max(120, H * 0.21)) / 278.71;
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    star.setAttribute('stroke-width', String(HAIR / s0));
    lines.forEach((ln) => {
      const [ax, ay] = unit(ln.a);
      const w = 40.55 * s0 * ln.sd;
      const mx = W / 2 - ay * w;
      const my = H / 2 + ax * w;
      let lo = -1e5;
      let hi = 1e5;
      for (const [a, m, size] of [
        [ax, mx, W],
        [ay, my, H],
      ]) {
        if (Math.abs(a) > 1e-9) {
          const t1 = -m / a;
          const t2 = (size - m) / a;
          lo = Math.max(lo, Math.min(t1, t2));
          hi = Math.min(hi, Math.max(t1, t2));
        }
      }
      ln.x0 = mx + ax * lo;
      ln.y0 = my + ay * lo;
      ln.x1 = mx + ax * hi;
      ln.y1 = my + ay * hi;
    });
    return (G = { W, H, s0 });
  }

  // The sidebar's logo, looked up once the app has had time to render under the intro:
  // undefined until then, null if none is showing. The rail and the open sidebar each draw one,
  // so every visible copy is held back until the mark lands.
  let target: HTMLElement | null | undefined;
  const marks: HTMLElement[] = [];
  let dock = false;
  function findTarget(): HTMLElement | null {
    for (const img of document.querySelectorAll<HTMLElement>('[data-intro-logo] img')) {
      if (shown(img)) marks.push(img);
    }
    if (marks.length) return marks[0];
    // A narrow window: the sidebar, and its logo, sit behind this button.
    const open = document.querySelector<HTMLElement>('[data-intro-dock]');
    if (open && shown(open)) {
      dock = true;
      return open;
    }
    return null;
  }
  function holdMarks(hidden: boolean) {
    marks.forEach((m) => (m.style.visibility = hidden ? 'hidden' : ''));
  }

  let T = still ? HOLD : 0;
  let end = HOLD + 1850;
  let drawn = -1;
  let last = 0;
  let rush = false;
  let raf = 0;

  function render(t: number) {
    const { W, H, s0 } = G ?? measure();
    if (target === undefined && t >= FLY0 && !still) {
      target = findTarget();
      if (target) {
        holdMarks(true); // the mark flies in to take their place
        end = FLY1 + 750;
      }
    }
    const glide = !!target;
    let x = W / 2;
    let y = H / 2;
    let sc = s0;
    if (target) {
      const tr = target.getBoundingClientRect();
      // Onto a logo: its exact size. Into the sidebar button: a mark the size of its icon,
      // which fades as it settles.
      const tx = tr.left + tr.width / 2;
      const ty = tr.top + tr.height / 2;
      const ts = (dock ? Math.min(tr.width, tr.height) * 0.72 : tr.width) / 278.71;
      const e = GLIDE(P(t, FLY0, FLY1));
      const vx = tx - W / 2;
      const vy = ty - H / 2;
      // A clear arc, not a straight line: it launches upward, then glides left.
      const qx = W / 2 + vx * 0.5 - vy * 0.17;
      const qy = H / 2 + vy * 0.5 + vx * 0.17;
      x = (1 - e) * (1 - e) * (W / 2) + 2 * (1 - e) * e * qx + e * e * tx;
      y = (1 - e) * (1 - e) * (H / 2) + 2 * (1 - e) * e * qy + e * e * ty;
      sc = s0 + (ts - s0) * e;
      if (t >= FLY1) {
        mg.style.display = 'none';
        holdMarks(false);
      }
      if (dock) {
        // The mark hands over to the button: one fades out as the other fades in.
        mg.setAttribute('opacity', String(1 - SOFT(P(t, FLY1 - 320, FLY1 - 40))));
        target.style.opacity = String(SOFT(P(t, FLY1 - 140, FLY1 + 220)));
      }
      const lp = P(t, FLY1, FLY1 + 750);
      const lk = 1 + OUT(lp);
      land.setAttribute(
        'transform',
        `translate(${tx} ${ty}) scale(${ts * lk}) translate(${-C} ${-C})`,
      );
      land.setAttribute('stroke-width', String(HAIR / (ts * lk)));
      land.setAttribute('opacity', String(lp > 0 && lp < 1 ? 0.45 * (1 - STD(lp)) : 0));
    }
    mg.setAttribute('transform', `translate(${x} ${y}) scale(${sc}) translate(${-C} ${-C})`);
    const bg = glide ? SOFT(P(t, FLY0 + 500, FLY1 + 150)) : SOFT(P(t, HOLD + 900, HOLD + 1800));
    ov.style.background = 'rgba(' + BG + ',' + (1 - bg) + ')';

    const p = P(t, 3300, 4200);
    const k = 1 + 0.28 * OUT(p);
    rip.setAttribute(
      'transform',
      `translate(${W / 2} ${H / 2}) scale(${s0 * k}) translate(${-C} ${-C})`,
    );
    rip.setAttribute('stroke-width', String(HAIR / (s0 * k)));
    rip.setAttribute('opacity', String(!still && p > 0 && p < 1 ? 0.3 * (1 - STD(p)) : 0));

    const snap = SOFT(P(t, 3000, 3450));
    const leave = !glide && !still;
    let rest = t <= HOLD || glide;
    cubes.forEach((cb, k) => {
      const q = P(t, DOCK[k], DOCK[k] + 1150);
      const o = OUT(q);
      const v = unit(DIR[k]);
      const c = CEN[k];
      // Leaving: pairs go in the order they docked, each easing out along its own line as a
      // solid cube again, then fading.
      const go = HOLD + 120 + ((DOCK[k] - DOCK[0]) / 200) * 220;
      const e = leave ? SOFT(P(t, go, go + 900)) : 0;
      const off = 260 * (1 - o) + 70 * e;
      const face = Math.max(1 - snap, leave ? 0.65 * SOFT(P(t, go, go + 260)) : 0);
      cb.g.setAttribute(
        'transform',
        `translate(${v[0] * off + c[0]} ${v[1] * off + c[1]}) rotate(${-120 * (1 - o)}) scale(${1 + 0.18 * (1 - o)}) translate(${-c[0]} ${-c[1]})`,
      );
      cb.g.setAttribute(
        'opacity',
        String(STD(P(q, 0, 0.22)) * (leave ? 1 - SOFT(P(t, go + 150, go + 900)) : 1)),
      );
      cb.fi.setAttribute('opacity', String(face * (LIT[k] ? 0.32 : 0.68)));
      cb.fs.setAttribute('opacity', String(face * 0.16));
      cb.gap.setAttribute('opacity', String(face));
      if (q < 1 || face > 0.001) rest = false;
    });
    const sd = SOFT(P(t, 850, 1400));
    star.setAttribute('stroke-dashoffset', String(100 - 100 * sd));
    star.setAttribute('opacity', String(sd > 0 ? 0.8 * (1 - STD(P(t, 1500, 1850))) : 0));
    const hq = P(t, 1250, 1700);
    const ho = OUT(hq);
    const core = leave ? SOFT(P(t, HOLD + 700, HOLD + 1500)) : 0; // the core goes last
    hub.setAttribute(
      'transform',
      `translate(${C} ${C}) scale(${(0.86 + 0.14 * ho) * (1 - 0.06 * core)}) translate(${-C} ${-C})`,
    );
    hub.setAttribute('opacity', String(STD(P(t, 1250, 1550)) * (1 - core)));
    if (hq < 1) rest = false;
    whole.style.display = rest ? '' : 'none';
    hub.style.display = rest ? 'none' : '';
    cubes.forEach((cb) => (cb.g.style.display = rest ? 'none' : ''));

    const fade = 1 - SOFT(P(t, 3000, 3450));
    lines.forEach((ln) => {
      const dd = OUT(P(t, ln.t0, ln.t0 + 1150));
      const oo = SOFT(P(t, 2950 + ln.t0 * 0.4, 3700 + ln.t0 * 0.4));
      ln.e.setAttribute('x1', String(ln.x0 + (ln.x1 - ln.x0) * oo));
      ln.e.setAttribute('y1', String(ln.y0 + (ln.y1 - ln.y0) * oo));
      ln.e.setAttribute('x2', String(ln.x0 + (ln.x1 - ln.x0) * dd));
      ln.e.setAttribute('y2', String(ln.y0 + (ln.y1 - ln.y0) * dd));
      ln.e.setAttribute('opacity', dd > 0 && oo < 1 ? '1' : '0');
    });
    const gb = 0.45 * STD(P(t, 650, 1100)) * fade;
    ghosts.forEach((gh) => gh.setAttribute('opacity', String(gb)));
    dots.forEach((dt) => {
      dt.e.setAttribute('r', (1.8 * OUT(P(t, 700 + 2 * dt.d, 1100 + 2 * dt.d)) * fade).toFixed(2));
    });
    ov.style.pointerEvents = t > (glide ? FLY0 + 500 : HOLD + 900) ? 'none' : '';
  }

  function finish() {
    cancelAnimationFrame(raf);
    holdMarks(false);
    if (dock && target) target.style.opacity = '';
    window.removeEventListener('resize', onResize);
    window.removeEventListener('keydown', onSkip, true);
    ov.removeEventListener('pointerdown', onSkip);
    ov.remove();
    playing = false;
  }
  function frame(now: number) {
    // Capped so a long stall while the app boots slows the intro instead of making it jump.
    const dt = last ? Math.min(100, now - last) : 0;
    last = now;
    if (T < HOLD) T = Math.min(HOLD, T + dt * (rush ? 6 : 1));
    else T += dt;
    if (T >= end) return finish();
    if (T !== drawn) render((drawn = T));
    raf = requestAnimationFrame(frame);
  }
  function onSkip() {
    rush = true;
  }
  function onResize() {
    G = null;
    render(T);
  }
  window.addEventListener('resize', onResize);
  window.addEventListener('keydown', onSkip, true);
  ov.addEventListener('pointerdown', onSkip);
  render((drawn = T));
  raf = requestAnimationFrame(frame);
}
