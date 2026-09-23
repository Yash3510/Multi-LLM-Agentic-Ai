<script>
	/*
	 * NodeGlyph - one node of the stage rail, also the mark at the start of the
	 * status line under it. Every state is the same ring:
	 * - not reached: a dotted ring, in the dashes of the wires;
	 * - working: six dots on the ring, a violet light running round them;
	 * - finished: the dots stretch along the ring until it closes, and a
	 *   centre dot comes up - amber when ULTRON sent the work back;
	 * - your decision: the closed ring in ink with a tick drawn in (released)
	 *   or a dash (withheld); a run cut off is an amber ring with a dash.
	 * `motion` plays the closing as the state changes; off, the glyph is drawn
	 * finished (an opened chat, reduced motion). Only changes after mounting
	 * play: a node that mounts already finished is drawn finished. `bloom`
	 * counts arrivals: each new value sends one soft ring off the node, the
	 * landing of the light that travelled the wire to it.
	 */
	export let kind = 'pending';
	export let motion = true;
	export let bloom = 0;

	const mountedAs = kind;
	const mountedBloom = bloom;
	let changed = false;
	$: if (kind !== mountedAs) changed = true;
	$: play = motion && changed;

	const C = 7;
	const R = 5.2;
	const PERIOD = 1.7; // seconds for the light to run once round the dots
	const DOTS = [0, 1, 2, 3, 4, 5].map((i) => {
		const a = ((-90 + 60 * i) * Math.PI) / 180;
		return [C + R * Math.cos(a), C + R * Math.sin(a)];
	});
	const TICK = 'M4.6 7.2l1.5 1.5 3-3.3';
	const DASH = 'M4.8 7h4.4';
	const CLOSED = new Set(['done', 'fail', 'released', 'withheld', 'interrupted']);
	const WAITING = new Set(['pending', 'requeued', 'skipped']);

	$: closed = CLOSED.has(kind);
	$: mark = kind === 'released' ? TICK : kind === 'withheld' || kind === 'interrupted' ? DASH : null;
</script>

<svg
	class="node-glyph k-{kind}"
	class:still={!play}
	viewBox="0 0 14 14"
	width="14"
	height="14"
	aria-hidden="true"
>
	<circle class="wait" class:on={WAITING.has(kind)} cx={C} cy={C} r={R} pathLength="60" />
	{#key bloom}
		{#if motion && bloom !== mountedBloom}
			<circle class="bloom" cx={C} cy={C} r={R} />
		{/if}
	{/key}
	{#if closed}
		<!-- Keyed on the kind, so a change between finished states (ULTRON's
		     verdict, your decision) closes the ring again in its new colour. -->
		{#key kind}
			<circle class="ring" cx={C} cy={C} r={R} pathLength="60" />
			{#if kind === 'done' || kind === 'fail'}
				<circle class="core" cx={C} cy={C} r="1.9" />
			{/if}
			{#if mark}
				<path class="mark" d={mark} pathLength="10" />
			{/if}
		{/key}
	{/if}
	<g class="spin" class:on={kind === 'active'}>
		{#each DOTS as [x, y], i}
			<circle cx={x} cy={y} r="1.2" style="animation-delay: {((i * PERIOD) / 6).toFixed(3)}s" />
		{/each}
		<circle class="hub" cx={C} cy={C} r="1" />
	</g>
</svg>

<style>
	.node-glyph {
		--ink: var(--color-gray-900, #1c1c1c);
		--done: var(--color-gray-700, #525252);
		--wire: var(--color-gray-300, #cdcdcd);
		--requeued: var(--color-gray-500, #9b9b9b);
		--amber: #f59e0b;
		--v-dot: #8b5cf6; /* violet-500: the working dots */
		--v-head: #7c3aed; /* violet-600: the dot the light is on, the hub */
		display: block;
		flex: none;
		overflow: visible;
	}
	:global(.dark) .node-glyph {
		--ink: #fff;
		--done: var(--color-gray-300, #cdcdcd);
		--wire: var(--color-gray-700, #525252);
		--requeued: var(--color-gray-500, #9b9b9b);
		--amber: #fbbf24;
		--v-dot: #a78bfa;
		--v-head: #ddd6fe;
	}

	/* Not reached: six dashes, each centred where a working dot will sit. */
	.wait {
		fill: none;
		stroke: var(--wire);
		stroke-width: 1;
		stroke-dasharray: 4 6;
		stroke-dashoffset: -3;
		opacity: 0;
		transition: opacity 600ms ease;
	}
	.wait.on {
		opacity: 1;
	}
	.k-requeued .wait {
		stroke: var(--requeued);
	}
	.k-skipped .wait {
		opacity: 0.5;
	}

	/* Working: the light runs round the six dots. Paused, not removed, when
	   the stage ends, so the dots fade out where they are. */
	.spin {
		opacity: 0;
		transition: opacity 600ms ease;
	}
	.spin.on {
		opacity: 1;
	}
	.spin circle {
		fill: var(--v-dot);
		opacity: 0.4;
		animation: dot-light 1.7s ease-in-out infinite;
		animation-play-state: paused;
	}
	.spin.on circle {
		animation-play-state: running;
	}
	.spin .hub {
		fill: var(--v-head);
		opacity: 1;
		animation: none;
	}

	/* Finished: the ring. Drawn closed at rest; `ring-close` starts it as the
	   six dots and stretches them round until they meet. */
	.ring {
		fill: none;
		stroke: var(--done);
		stroke-width: 1.25;
		stroke-linecap: round;
		transition: stroke 300ms ease;
		animation: ring-close 1.4s both;
	}
	.core {
		fill: var(--done);
		transition: fill 300ms ease;
		transform-box: fill-box;
		transform-origin: center;
		animation: core-in 1s 450ms cubic-bezier(0.65, 0, 0.35, 1) both;
	}
	.mark {
		fill: none;
		stroke: var(--ink);
		stroke-width: 1.35;
		stroke-linecap: round;
		stroke-linejoin: round;
		stroke-dasharray: 10;
		animation: mark-draw 900ms 1.1s cubic-bezier(0.45, 0, 0.2, 1) both;
	}
	.k-fail .ring,
	.k-interrupted .ring {
		stroke: var(--amber);
	}
	.k-fail .core {
		fill: var(--amber);
	}
	.k-interrupted .mark {
		stroke: var(--amber);
	}
	.k-released .ring,
	.k-withheld .ring {
		stroke: var(--ink);
	}

	/* The light landing: one soft ring off the node. */
	.bloom {
		fill: none;
		stroke: var(--v-head);
		stroke-width: 1;
		vector-effect: non-scaling-stroke;
		transform-box: fill-box;
		transform-origin: center;
		animation: bloom 1.5s cubic-bezier(0.22, 1, 0.36, 1) both;
	}

	.still .ring,
	.still .core,
	.still .mark {
		animation: none;
	}

	@keyframes dot-light {
		0% {
			opacity: 1;
			fill: var(--v-head);
		}
		35% {
			opacity: 0.7;
		}
		70%,
		100% {
			opacity: 0.4;
		}
	}
	@keyframes ring-close {
		0% {
			opacity: 0;
			stroke-width: 2.4;
			stroke-dasharray: 0 10;
			stroke-dashoffset: 5;
			animation-timing-function: ease;
		}
		30% {
			opacity: 1;
			stroke-width: 2.4;
			stroke-dasharray: 0 10;
			stroke-dashoffset: 5;
			animation-timing-function: cubic-bezier(0.65, 0, 0.35, 1);
		}
		100% {
			opacity: 1;
			stroke-width: 1.25;
			stroke-dasharray: 10 0;
			stroke-dashoffset: 10;
		}
	}
	@keyframes core-in {
		from {
			opacity: 0;
			transform: scale(0.5);
		}
	}
	@keyframes mark-draw {
		from {
			stroke-dashoffset: 10;
		}
		to {
			stroke-dashoffset: 0;
		}
	}
	@keyframes bloom {
		from {
			opacity: 0.45;
			transform: scale(1);
		}
		to {
			opacity: 0;
			transform: scale(1.8);
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.ring,
		.core,
		.mark,
		.bloom {
			animation: none;
		}
		.bloom {
			opacity: 0;
		}
		/* Still say which stage is working, without the running light. */
		.spin circle {
			animation: none;
			opacity: 0.7;
		}
	}
</style>
