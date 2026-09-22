<script>
	/*
	 * ThinkingOrb — a Svelte binding over the `thinking-orbs` engine.
	 *
	 * The package ships a React component, but it also exports its engine as a
	 * deliberately framework-free surface ("the portable surface: pure geometry,
	 * no canvas", per its own types) so that non-React ports render identically
	 * by construction rather than by re-implementation. That is what this binds
	 * to: the animations, presets and tuning are the package's, and only the
	 * canvas, rAF and theme glue is ours — so no React enters the bundle of an
	 * application whose point is running lean and offline.
	 *
	 * thinking-orbs is MIT, (c) 2026 Jakub Antalik.
	 */
	import { onMount, onDestroy } from 'svelte';
	import { MODE_DRAWS, resolvePreset } from 'thinking-orbs/engine';

	/** One of the nine shipped states. */
	export let state = 'working';
	/** Tuned preset: 64 (avatar scale) or 20 (inline-text scale). */
	export let size = 20;
	/** Multiplier on the preset's baked speed. */
	export let speed = 1;
	/** Freeze on the current frame. */
	export let paused = false;
	/** Accessible label; defaults to the state verb. */
	export let label = null;
	/*
	 * Rendered CSS size, when it should differ from the preset being drawn.
	 * The package ships two tuned designs — 64 (chat-avatar) and 20 (inline) —
	 * which are separate designs rather than a scale factor, so this picks the
	 * 64 design and lays it out smaller rather than thinning the 20 one. The
	 * canvas backing store still scales by DPR, so it stays crisp.
	 */
	export let display = null;
	/*
	 * Ink density on light backgrounds: how many times each frame is drawn.
	 * The package depth-shades back-facing dots with low alpha, which reads well
	 * on dark but washes out on white at avatar size - `searching`, the FRIDAY
	 * stage, paints at a mean alpha of about 28%. Drawing the same frame twice
	 * compounds alpha (28% to about 48%) while leaving every shape and depth
	 * ratio exactly as designed. Dark themes are left at 1.
	 */
	export let lightInk = 1;
	export let className = '';

	let canvas;
	let ctx = null;
	let raf = 0;
	let t0 = 0;
	let lastT = 0;
	let dark = false;
	let reduced = false;
	let mounted = false;

	let themeObserver;
	let schemeQuery;
	let motionQuery;

	// The app writes `dark` / `light` onto <html>; fall back to the OS setting.
	const resolveTheme = () => {
		if (typeof document === 'undefined') return false;
		const root = document.documentElement;
		if (root.classList.contains('dark')) return true;
		if (root.classList.contains('light')) return false;
		return schemeQuery ? schemeQuery.matches : false;
	};

	const resize = () => {
		if (!canvas) return;
		const css = display ?? size;
		// Enough backing pixels for the laid-out size, at the DPR we render at.
		const dpr = Math.min(window.devicePixelRatio || 1, 2) * (css / size);
		canvas.width = Math.round(size * dpr);
		canvas.height = Math.round(size * dpr);
		canvas.style.width = `${css}px`;
		canvas.style.height = `${css}px`;
		const next = canvas.getContext('2d');
		if (next) next.setTransform(dpr, 0, 0, dpr, 0, 0);
		ctx = next;
	};

	const draw = (t) => {
		if (!ctx) return;
		/* Never negative. A rAF timestamp can land a few ms before the
		   performance.now() the clock was started from, and the engine's
		   `morph` mode (the `shaping` state) throws on negative time - measured:
		   the other eight states tolerate it, morph does not, at either size. */
		t = Math.max(0, t);
		lastT = t;
		const preset = resolvePreset(state, size);
		const passes = dark ? 1 : Math.max(1, Math.round(lightInk));
		ctx.clearRect(0, 0, size, size);
		try {
			for (let i = 0; i < passes; i++) {
				MODE_DRAWS[preset.mode](ctx, size, t * preset.speed, dark, preset.opts);
			}
		} catch (err) {
			/* One bad frame must not end the animation. Before this guard a throw
			   escaped the rAF callback before the next frame was requested, so the
			   loop died with the canvas already cleared: a blank orb for the rest
			   of the run. */
		}
	};

	const loop = (now) => {
		if (!t0) t0 = now;
		draw(((now - t0) / 1000) * speed);
		raf = requestAnimationFrame(loop);
	};

	const stop = () => {
		if (raf) cancelAnimationFrame(raf);
		raf = 0;
	};

	/* Restart the animation. It paints a frame synchronously before handing
	   over to rAF: waiting for the next frame left the canvas blank for one or
	   two frames, which read as a flicker every time the orb appeared. It also
	   resumes from the current time rather than 0, so nothing snaps back.
	   Paused, or a reader who asked for reduced motion, gets one settled frame
	   rather than nothing - the orb still names the stage, it just holds still. */
	const restart = () => {
		stop();
		draw(lastT);
		if (paused || reduced) return;
		t0 = performance.now() - (lastT / (speed || 1)) * 1000;
		raf = requestAnimationFrame(loop);
	};

	onMount(() => {
		schemeQuery = window.matchMedia('(prefers-color-scheme: dark)');
		motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
		reduced = motionQuery.matches;
		dark = resolveTheme();

		const onScheme = () => {
			dark = resolveTheme();
			restart();
		};
		const onMotion = () => {
			reduced = motionQuery.matches;
			restart();
		};
		schemeQuery.addEventListener('change', onScheme);
		motionQuery.addEventListener('change', onMotion);

		themeObserver = new MutationObserver(() => {
			const next = resolveTheme();
			if (next !== dark) {
				dark = next;
				restart();
			}
		});
		themeObserver.observe(document.documentElement, {
			attributes: true,
			attributeFilter: ['class']
		});

		resize();
		mounted = true;
		restart();

		return () => {
			schemeQuery.removeEventListener('change', onScheme);
			motionQuery.removeEventListener('change', onMotion);
		};
	});

	onDestroy(() => {
		stop();
		themeObserver?.disconnect();
	});

	/* Size changes rebuild the backing store, which clears the canvas, so they
	   repaint immediately. Neither block may read `ctx`: `resize()` reassigns
	   it, and a read would make the block its own dependency.

	   A change of stage needs nothing here. The loop reads `state` and
	   `lightInk` on every frame, so it simply draws the new stage next frame.
	   Rebuilding the canvas on each stage change used to blank it for a frame
	   at every transition of the agent chain. */
	$: if (mounted) {
		size;
		display;
		resize();
		draw(lastT);
	}

	$: if (mounted) {
		paused;
		restart();
	}

	/* With no loop running, a stage change still has to be painted. */
	$: if (mounted && (paused || reduced)) {
		state;
		lightInk;
		draw(lastT);
	}
</script>

<canvas
	bind:this={canvas}
	class={className}
	role="img"
	aria-label={label ?? `${state}…`}
	style="display:block"
></canvas>
