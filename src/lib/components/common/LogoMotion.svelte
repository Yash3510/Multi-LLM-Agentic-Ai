<script>
	/*
	 * LogoMotion - the 4CE mark, animated while the agent chain works. It
	 * replaces the thinking orb; its motions (MOTIONS in logoMotion.js) move
	 * pieces of the traced artwork itself.
	 *
	 * Every motion loops from and back to the exact mark, so a list of them
	 * hands from one to the next at the end of a loop without a seam. A new
	 * list, or `motion` going null, first eases the current motion back to the
	 * still mark (SETTLE_MS), so it never jumps; at rest it draws exactly what
	 * the logo image draws, which lets the chat swap the two.
	 */
	import { onDestroy } from 'svelte';
	import {
		MARK,
		OUTLINE,
		HOLES,
		C,
		VIEW,
		LIT,
		CENTRES,
		MOTIONS,
		SOFT,
		pieceClip,
		hubClip,
		hexPoints,
		axis,
		rest,
		settle,
		isRest,
		onFrame
	} from './logoMotion.js';

	/** A key of MOTIONS, a list of them to take turns, or null for the still mark. */
	export let motion = null;
	/** Rendered size of the mark itself, in px. */
	export let size = 30;
	/** Start a list at a random motion, so side-by-side marks differ. */
	export let randomStart = false;
	/** Accessible label; without one the mark is decorative. */
	export let label = null;
	export let className = '';

	const SETTLE_MS = 320;
	const ORDER = [1, 3, 5, 0, 2, 4]; // open-faced cubes on top, since they slide over the rest
	const uid = `lm${Math.random().toString(36).slice(2, 8)}`;
	const offset = (VIEW - 278.71) / 2;

	$: box = (size * VIEW) / 278.71;
	/* Small marks move further: at avatar size a 10-unit nudge is one pixel,
	   which reads as nothing happening. Outward moves and lifts scale up to
	   2.4x below 64px; inward slides are exact and never scaled. */
	$: amp = Math.min(2.4, Math.max(1, 64 / size));
	$: linePx = size < 48 ? 1 : Math.max(0.5, 1 / (typeof window === 'undefined' ? 1 : window.devicePixelRatio || 1));

	let markEl, wholeEl, hubEl, echoEl;
	let cubeEls = [];
	let faceEls = [];
	let sideEls = [];
	let gapEls = [];

	let list = []; // the motions to take turns with
	let turn = 0;
	let active = null; // motion being played
	let started = 0;
	let settling = null; // { from, start }
	let stop = null;

	const reduced = () =>
		typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

	function current(now) {
		if (settling) return settle(settling.from, SOFT((now - settling.start) / SETTLE_MS));
		if (active) {
			const m = MOTIONS[active];
			return m.at((now - started) % m.period);
		}
		return rest();
	}

	const firstTurn = () => (randomStart ? Math.floor(Math.random() * list.length) : 0);

	function request(wanted) {
		if (!markEl) return;
		const next = (Array.isArray(wanted) ? wanted : [wanted]).filter((m) => m && MOTIONS[m]);
		if (next.join() === list.join()) return;
		list = reduced() ? [] : next;
		const now = performance.now();
		if (active && list.includes(active)) {
			// Still in the list: keep the loop that is playing.
			turn = list.indexOf(active);
		} else if (active) {
			settling = { from: current(now), start: now };
			active = null;
		} else if (!settling && list.length) {
			turn = firstTurn();
			active = list[turn];
			started = now;
		}
		if ((active || settling) && !stop) stop = onFrame(frame);
	}
	$: request(motion), markEl;

	function frame(now) {
		if (settling && now - settling.start >= SETTLE_MS) {
			settling = null;
			if (list.length) {
				turn = firstTurn();
				active = list[turn];
				started = now;
			}
		} else if (active && now - started >= MOTIONS[active].period) {
			// A loop ends on the still mark: hand over to the next motion here.
			started += MOTIONS[active].period;
			if (now - started >= MOTIONS[active].period) started = now;
			turn = (turn + 1) % list.length;
			active = list[turn];
		}
		draw(current(now));
		if (!active && !settling) {
			stop?.();
			stop = null;
		}
	}

	function draw(s) {
		const still = isRest(s);
		markEl.setAttribute('transform', `rotate(${s.mark} ${C} ${C})`);
		wholeEl.style.display = still ? '' : 'none';
		hubEl.style.display = still ? 'none' : '';
		hubEl.setAttribute(
			'transform',
			`rotate(${s.hub} ${C} ${C}) translate(${C} ${C}) scale(${s.hubScale}) translate(${-C} ${-C})`
		);
		s.cubes.forEach((c, k) => {
			const [ux, uy] = axis(k);
			const [cx, cy] = CENTRES[k];
			const g = cubeEls[k];
			const off = c.off > 0 ? c.off * amp : c.off;
			const sc = 1 + (c.sc - 1) * amp;
			g.style.display = still ? 'none' : '';
			g.setAttribute(
				'transform',
				`rotate(${c.orb} ${C} ${C}) translate(${ux * off + cx} ${uy * off + cy}) rotate(${c.rot}) scale(${sc}) translate(${-cx} ${-cy})`
			);
			// Shaded strongly enough to read as a solid block at 30px.
			faceEls[k].setAttribute('opacity', c.face * (LIT[k] ? 0.48 : 0.88));
			sideEls[k].setAttribute('opacity', c.face * 0.26);
			gapEls[k].setAttribute('opacity', c.gap ?? Math.min(1, c.face * 1.4));
		});
		echoEl.setAttribute('opacity', s.echo);
		if (s.echo > 0) {
			echoEl.setAttribute('transform', `translate(${C} ${C}) scale(${s.echoScale}) translate(${-C} ${-C})`);
			echoEl.setAttribute('stroke-width', linePx / ((size / 278.71) * s.echoScale));
		}
	}

	onDestroy(() => stop?.());
</script>

<svg
	class="shrink-0 {className}"
	style="overflow: visible"
	width={box}
	height={box}
	viewBox="{-offset} {-offset} {VIEW} {VIEW}"
	role={label ? 'img' : undefined}
	aria-label={label ?? undefined}
	aria-hidden={label ? undefined : 'true'}
>
	<defs>
		{#each [0, 1, 2, 3, 4, 5] as k}
			<clipPath id="{uid}-p{k}"><polygon points={pieceClip(k)} /></clipPath>
		{/each}
		<clipPath id="{uid}-hub"><polygon points={hubClip} /></clipPath>
	</defs>
	<path bind:this={echoEl} class="lm-line" d={OUTLINE} fill="none" opacity="0" />
	<g bind:this={markEl}>
		<path bind:this={wholeEl} class="lm-ink" d={MARK} fill-rule="evenodd" />
		<path
			bind:this={hubEl}
			class="lm-ink"
			d={MARK}
			fill-rule="evenodd"
			clip-path="url(#{uid}-hub)"
			style="display: none"
		/>
		{#each ORDER as k}
			<g bind:this={cubeEls[k]} style="display: none">
				<polygon bind:this={gapEls[k]} class="lm-gap" points={hexPoints(k)} opacity="0" />
				<path class="lm-ink" d={MARK} fill-rule="evenodd" clip-path="url(#{uid}-p{k})" />
				{#if LIT[k]}
					<!-- The open face, filled while the cube moves so it reads as solid. -->
					<path bind:this={faceEls[k]} class="lm-ink" d={HOLES[k]} opacity="0" />
					<path
						bind:this={sideEls[k]}
						class="lm-paper"
						d={HOLES[k]}
						opacity="0"
						transform="rotate(120 {CENTRES[k][0]} {CENTRES[k][1]})"
					/>
				{:else}
					<!-- A solid cube's inner face: the opposite cube's hole, turned into place. -->
					<path
						bind:this={faceEls[k]}
						class="lm-paper"
						d={HOLES[(k + 3) % 6]}
						opacity="0"
						transform="rotate(180 {C} {C})"
					/>
					<path
						bind:this={sideEls[k]}
						class="lm-paper"
						d={HOLES[(k + 3) % 6]}
						opacity="0"
						transform="rotate(120 {CENTRES[k][0]} {CENTRES[k][1]}) rotate(180 {C} {C})"
					/>
				{/if}
			</g>
		{/each}
	</g>
</svg>

<style>
	/* The logo images' own inks (static/logo-mark-dark.svg / -light.svg), and
	   the chat's background for the faces and the cut line round a moving cube. */
	.lm-ink {
		fill: #0d1117;
	}
	.lm-paper {
		fill: #fff;
	}
	.lm-gap {
		fill: none;
		stroke: #fff;
		stroke-width: 5;
		stroke-linejoin: round;
	}
	.lm-line {
		stroke: rgba(13, 17, 23, 0.55);
	}
	:global(.dark) .lm-ink {
		fill: #fff;
	}
	:global(.dark) .lm-paper {
		fill: var(--color-gray-900, #161616);
	}
	:global(.dark) .lm-gap {
		stroke: var(--color-gray-900, #161616);
	}
	:global(.dark) .lm-line {
		stroke: rgba(255, 255, 255, 0.55);
	}
</style>
