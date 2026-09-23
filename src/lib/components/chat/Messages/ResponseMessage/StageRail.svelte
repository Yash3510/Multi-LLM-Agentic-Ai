<script>
	/*
	 * StageRail - the 4CE agent chain as a node path at the top of each answer:
	 *   TONY ◉ ╌╌ ◉ FRIDAY ╌╌ ⁘ JARVIS ╌╌ ◌ ULTRON ╌╌ ◌ You
	 * Every node is one ring (NodeGlyph): dotted before its stage runs, six
	 * violet dots while it works, closed with a centre dot once it is done,
	 * and at the gate a ring with a tick when you release or a dash when you
	 * withhold. The wires are dashed hairlines.
	 *
	 * A live run hands over one stage at a time, never in a hurry: the
	 * finished node closes its ring, then a soft light leaves it and glides
	 * along the wire, filling it as it goes, and stops at the next node. Only
	 * when it lands does that node start working. The rail can trail the run
	 * by a handover (about three seconds); a replan jumps straight back, with
	 * the arc from ULTRON showing the way.
	 *
	 * Built only from the status stream the orchestrator already sends, so it
	 * shows what actually happened rather than a canned animation:
	 * - completed stages show how long they took, from the server timestamp
	 *   `_status()` attaches (`ts`) - measured, not estimated, and kept with
	 *   the message, so a reloaded chat still shows its timings;
	 * - the running stage counts up live from when its status reached this
	 *   browser, so a clock mismatch between server and browser cannot show;
	 * - a failed ULTRON challenge and each replan are visible, with time in a
	 *   stage summed across passes;
	 * - "You" is the human gate: reviewing, released, or withheld.
	 *
	 * Direct replies ("hi") never reach the chain, so they get no rail. An
	 * opened chat draws its rail finished, without motion.
	 */
	import { onDestroy } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import NodeGlyph from './NodeGlyph.svelte';

	export let statusHistory = [];
	export let done = false;
	/** Where the rail is, for the status line under it (bound by the message). */
	export let live = null;

	const STAGE_OF = {
		tony_plan: 'TONY',
		tony: 'TONY',
		router: 'TONY',
		tony_replan: 'TONY',
		friday: 'FRIDAY',
		jarvis: 'JARVIS',
		ultron: 'ULTRON',
		approval: 'You'
	};
	const ORDER = ['TONY', 'FRIDAY', 'JARVIS', 'ULTRON', 'You'];
	// Statuses that end whatever stage is running.
	const CLOSING = new Set(['done', 'stopped', 'error', 'tool']);

	// Mounted finished (an opened chat): drawn as it ended, with no motion.
	const cascade = done;
	const reduced =
		typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
	const motion = !cascade && !reduced;

	// The handover, in ms: the finished node closes its ring, then the light
	// leaves, glides the wire, and fades into the next node as it lands.
	const LEAVE = 950;
	const TRAVEL = 1900;
	const FADE = 550;

	let root;
	let now = Date.now();
	let timer = null;
	// When each status reached this browser - live runs only.
	const arrivals = [];

	$: entries = (statusHistory ?? []).filter(Boolean);
	$: if (!done) {
		for (let i = arrivals.length; i < entries.length; i++) arrivals[i] = Date.now();
	}

	function derive(entries, done, now) {
		const segs = [];
		let replans = 0;
		let ultronFail = false;
		let outcome = null; // 'withheld' | 'released'
		let endedBy = null; // 'stopped' | 'error'
		let endedStage = null;

		const close = (ts) => {
			const cur = segs[segs.length - 1];
			if (cur && cur.end === undefined) cur.end = ts ?? null;
		};

		entries.forEach((e, i) => {
			const a = e.action;
			if (a === 'tony_replan') replans += 1;
			const pass = replans;
			if (a === 'ultron' && /FAIL|PASS/.test(e.description ?? '')) {
				ultronFail = /FAIL/.test(e.description);
			}
			const stage = STAGE_OF[a];
			if (stage) {
				const cur = segs[segs.length - 1];
				if (!cur || cur.stage !== stage || cur.end !== undefined) {
					close(e.ts);
					segs.push({ stage, start: e.ts ?? null, idx: i, end: undefined, pass });
				}
				if (stage === 'You' && e.done) {
					outcome = 'withheld';
					close(e.ts);
				}
			} else if (CLOSING.has(a)) {
				if (a === 'stopped' || a === 'error') {
					endedBy = a;
					endedStage = segs[segs.length - 1]?.stage ?? null;
				}
				if (a === 'tool' || a === 'done') {
					if (segs.some((s) => s.stage === 'You') && outcome === null) outcome = 'released';
				}
				close(e.ts);
			}
		});

		const last = segs[segs.length - 1];
		const running = !done && !!last && last.end === undefined;
		const interrupted = done && !!last && last.end === undefined;

		const liveSecs = (seg) => {
			if (arrivals[seg.idx]) return Math.max(0, (now - arrivals[seg.idx]) / 1000);
			return seg.start != null ? Math.max(0, now / 1000 - seg.start) : 0;
		};

		const stages = ORDER.map((name) => {
			const mine = segs.filter((s) => s.stage === name);
			let state;
			if (!mine.length) state = done ? 'skipped' : 'pending';
			else if (running && last.stage === name) state = 'active';
			else if (interrupted && last.stage === name) state = 'interrupted';
			else state = 'done';

			// Sent back by a replan and waiting to run again: it drops back to the
			// waiting look, then lights up again as the new pass reaches it.
			if (
				running &&
				RERUN.has(name) &&
				state !== 'active' &&
				mine.length &&
				mine[mine.length - 1].pass < replans
			) {
				state = 'requeued';
			}

			// A stopped or failed run must not read as a tick on the stage it ended in.
			if (name === endedStage && state === 'done') state = 'interrupted';
			if (name === 'ULTRON' && state === 'done' && ultronFail) state = 'fail';
			if (name === 'You' && state === 'done' && outcome) state = outcome;

			let secs = 0;
			let known = false;
			for (const s of mine) {
				if (s.end === undefined && state === 'active') {
					secs += liveSecs(s);
					known = true;
				} else if (s.start != null && s.end != null) {
					secs += s.end - s.start;
					known = true;
				}
			}

			const ended = endedBy === 'stopped' ? 'stopped' : endedBy === 'error' ? 'failed' : 'interrupted';
			const note =
				state === 'interrupted'
					? name === endedStage
						? ended
						: 'interrupted'
					: name === 'You'
						? { active: 'reviewing', released: 'released', withheld: 'withheld' }[state] ?? null
						: state === 'fail'
							? 'fail'
							: null;

			// Passes through this stage: after a replan FRIDAY, JARVIS and ULTRON
			// each run again, and their times above are totals across passes.
			const runs = RERUN.has(name) ? mine.length : 1;
			return { name, state, time: known ? fmt(secs) : null, secs: known ? secs : null, note, runs };
		});

		const inChain = segs.some((s) => ['FRIDAY', 'JARVIS', 'ULTRON'].includes(s.stage));
		return { stages, replans, running, inChain };
	}

	// The stages a replan sends the work back through.
	const RERUN = new Set(['FRIDAY', 'JARVIS', 'ULTRON']);
	const ordinal = (n) =>
		n + (n % 100 >= 11 && n % 100 <= 13 ? 'th' : ({ 1: 'st', 2: 'nd', 3: 'rd' }[n % 10] ?? 'th'));

	function fmt(s) {
		if (s < 0.1) return '<0.1s';
		if (s < 60) return `${s.toFixed(1)}s`;
		const m = Math.floor(s / 60);
		return `${m}m ${String(Math.round(s % 60)).padStart(2, '0')}s`;
	}

	$: view = derive(entries, done, now);

	/* Tick only while something is running. A function rather than an inline
	   reactive block: `view` depends on `now`, so a block that both reads
	   `view` and writes `now` is a cycle the compiler rejects. */
	function syncTimer(running) {
		if (running && !timer) {
			timer = setInterval(() => (now = Date.now()), 100);
		} else if (!running && timer) {
			clearInterval(timer);
			timer = null;
			now = Date.now();
		}
	}
	$: syncTimer(view.running);

	/* The handover. `shown` is the stage the rail has reached; it chases the
	   run's frontier (the working stage, or the last one reached) one wire at
	   a time. Stages past it still look unreached, whatever the run says. */
	const UNREACHED = new Set(['pending', 'skipped', 'requeued']);
	function frontierOf(stages) {
		const working = stages.findIndex((s) => s.state === 'active');
		if (working >= 0) return working;
		let last = -1;
		stages.forEach((s, i) => {
			if (!UNREACHED.has(s.state)) last = i;
		});
		return last;
	}
	$: frontier = frontierOf(view.stages);

	let shown = -1;
	let travelling = -1; // the wire carrying the light
	let landings = ORDER.map(() => 0);
	let busy = false;
	let pending = [];
	const after = (ms, fn) => pending.push(setTimeout(fn, ms));
	function cancel() {
		pending.forEach(clearTimeout);
		pending = [];
		busy = false;
		travelling = -1;
	}

	function chase(target) {
		if (cascade || target < 0) return;
		// First sight of a run (a new answer, or a run already under way when
		// the chat was opened): start where it is, without replaying it.
		if (shown < 0 || !motion) {
			shown = target;
			return;
		}
		// Sent back by a replan: straight there; the arc shows the way back.
		if (target < shown) {
			cancel();
			shown = target;
			landings[shown] += 1;
			return;
		}
		if (busy || target === shown) return;
		busy = true;
		const from = shown;
		after(LEAVE, () => (travelling = from));
		after(LEAVE + TRAVEL, () => {
			shown = from + 1;
			landings[shown] += 1;
			busy = false;
			chase(frontier);
		});
		after(LEAVE + TRAVEL + FADE, () => {
			if (travelling === from) travelling = -1;
		});
	}
	$: chase(frontier);

	$: looks = view.stages.map((s, i) =>
		cascade || i <= shown ? s.state : UNREACHED.has(s.state) ? s.state : 'pending'
	);

	/* One-shot moments of a live run. A replan fires a spark back along the arc
	   to FRIDAY - its own event, because on a real run FRIDAY starts again
	   within milliseconds of the replan, so there is no replan stage long
	   enough to animate. A release sends one light across the names. */
	let arcWidth = 0;
	let sparkKey = 0;
	let seenReplans = cascade ? Infinity : 0;
	function syncSpark(replans) {
		if (replans > seenReplans) sparkKey += 1;
		seenReplans = Math.max(seenReplans === Infinity ? replans : seenReplans, replans);
	}
	$: syncSpark(view.replans);

	let sweeping = false;
	let sweepTimer = null;
	let swept = cascade;
	function syncSweep(gate) {
		if (swept || gate !== 'released') return;
		swept = true;
		sweeping = true;
		// The ring closes, the tick draws, then the light crosses the names.
		sweepTimer = setTimeout(() => (sweeping = false), 5800);
	}
	$: syncSweep(looks[looks.length - 1]);

	onDestroy(() => {
		timer && clearInterval(timer);
		clearTimeout(sweepTimer);
		cancel();
	});

	/* For the status line: the stage the rail is on, the handover while the
	   light travels, how the run ended and the agents' working time. Passed on only when it changes:
	   the rail re-derives on every streamed token, and a fresh object each
	   time would update the line under it just as often. */
	let liveKey = '';
	function report(next) {
		const key = JSON.stringify(next);
		if (key === liveKey) return;
		liveKey = key;
		live = next;
	}
	$: report({
		stage: shown >= 0 ? view.stages[shown]?.name : null,
		working: shown >= 0 && looks[shown] === 'active',
		handover:
			!cascade && shown >= 0 && frontier > shown
				? { from: view.stages[shown].name, to: view.stages[shown + 1]?.name }
				: null,
		// The agent a failed or stopped run ended at.
		stoppedAt:
			view.stages.find((s) => s.state === 'interrupted' && (s.note === 'failed' || s.note === 'stopped'))
				?.name ?? null,
		// The agents' working time, without your time reviewing.
		worked: (() => {
			const agents = view.stages.filter((s) => s.name !== 'You' && s.secs != null);
			return agents.length ? fmt(agents.reduce((sum, s) => sum + s.secs, 0)) : null;
		})(),
		outcome: view.stages.some((s) => s.state === 'interrupted')
			? 'interrupted'
			: ['released', 'withheld'].includes(view.stages[view.stages.length - 1].state)
				? view.stages[view.stages.length - 1].state
				: null,
		inChain: view.inChain
	});

	/* The arc's width, read straight away and then on resize. bind:clientWidth
	   waits for the first ResizeObserver report, which only comes with a drawn
	   frame, so the arc appeared a frame late (or never, in a hidden tab). */
	function measure(node) {
		const read = () => (arcWidth = node.clientWidth);
		read();
		const observer = new ResizeObserver(read);
		observer.observe(node);
		return { destroy: () => observer.disconnect() };
	}
	$: arcPath = arcWidth ? `M${arcWidth} 22 C ${arcWidth * 0.86} 1, ${arcWidth * 0.14} 1, 0 22` : '';

	/* Open what a stage produced. FRIDAY and ULTRON each have a collapsible
	   section in the finished answer; the rest scroll to the provenance table. */
	function openStage(name) {
		const msg = root?.closest('[id^="message-"]');
		if (!msg) return;
		const prefix = { FRIDAY: 'FRIDAY —', ULTRON: 'ULTRON —' }[name];
		if (prefix) {
			const btn = [...msg.querySelectorAll('button')].find((b) =>
				b.textContent.trim().startsWith(prefix)
			);
			if (btn) {
				if (btn.getAttribute('aria-expanded') !== 'true') btn.click();
				btn.scrollIntoView({ behavior: 'smooth', block: 'center' });
				return;
			}
		}
		const prov = [...msg.querySelectorAll('h1, h2, h3, h4')].find((h) =>
			/4CE provenance/.test(h.textContent)
		);
		prov?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	/* Label colour per state. */
	const LABEL = {
		done: 'text-gray-800 dark:text-gray-100',
		active: 'text-gray-900 dark:text-white',
		pending: 'text-gray-500 dark:text-gray-500',
		requeued: 'text-gray-500 dark:text-gray-400',
		skipped: 'text-gray-300 dark:text-gray-600',
		fail: 'text-amber-700 dark:text-amber-300',
		withheld: 'text-gray-800 dark:text-gray-100',
		interrupted: 'text-amber-700 dark:text-amber-300',
		released: 'text-gray-900 dark:text-white'
	};

	/* The wire leaving stage i, toward stage i + 1. */
	function wire(stages, i) {
		const from = stages[i];
		const to = stages[i + 1];
		if (from.state === 'active') return 'future';
		if (to.name === 'You') {
			// Your decision, either way, fills the wire in ink; only a run cut
			// off before you decided turns it amber.
			if (to.state === 'released' || to.state === 'withheld') return 'released';
			if (to.state === 'interrupted') return 'held';
		}
		if (UNREACHED.has(to.state)) return 'future';
		return 'done';
	}
	// A wire the rail has not crossed yet stays dashed.
	$: wires = view.stages
		.slice(0, -1)
		.map((_, i) => (cascade || i < shown ? wire(view.stages, i) : 'future'));
</script>

{#if view.inChain}
	<!-- Flush with the text column: TONY's node sits on the same left edge as
	     the model name and the answer, and each label starts under its node.
	     The four agents share the width; YOU takes what its label needs, so
	     the gate always ends the rail. -->
	<div
		bind:this={root}
		class="rail relative mb-3 w-full max-w-[34rem] {view.replans > 0 ? 'pt-9' : 'pt-2.5'}"
		class:sweeping
		in:fade={{ duration: motion ? 420 : 0 }}
	>
		{#if view.replans > 0}
			<span class="sr-only">
				ULTRON sent the draft back {view.replans > 1 ? `${view.replans} times` : 'once'}; FRIDAY,
				JARVIS and ULTRON ran again. This is the {ordinal(view.replans + 1)} try.
			</span>
		{/if}

		<div
			class="relative grid grid-cols-[repeat(4,minmax(0,1fr))_auto]"
			role="list"
			aria-label="Agent chain"
		>
			{#if view.replans > 0}
				<!-- One faint arc from ULTRON back to FRIDAY: the self-correction,
				     visible without crowding the path. Placed on the grid itself,
				     FRIDAY's column to ULTRON's, so it meets both nodes at any
				     width. While the run is live a spark travels it back once. -->
				<div
					class="pointer-events-none absolute col-start-2 col-end-4 row-start-1 -top-[22px] left-[7px] right-[-7px] h-[22px]"
					use:measure
					aria-hidden="true"
				>
					<!-- Drawn in real pixels (the box's measured width), not a stretched
					     viewBox: stretched, the cut lines and the spark ran at uneven
					     speed round the curve. -->
					{#if arcPath}
						<svg
							class="replan h-full w-full overflow-visible text-amber-400 dark:text-amber-600"
							viewBox="0 0 {arcWidth} 22"
						>
							<path d={arcPath} fill="none" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 3" />
							{#key sparkKey}
								{#if sparkKey}
									<!-- The objection travelling back to FRIDAY, once. -->
									<path
										class="arc-spark text-amber-500 dark:text-amber-300"
										d={arcPath}
										pathLength="100"
										fill="none"
										stroke="currentColor"
										stroke-width="2.5"
										stroke-linecap="round"
										stroke-dasharray="10 100"
									/>
								{/if}
							{/key}
						</svg>
					{/if}
					<span
						class="absolute -top-[10px] left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px] leading-[15px] tracking-wide text-amber-700 dark:text-amber-300"
					>
						<!-- Plain words: "replanned" alone did not say who sent the work
						     back or that it ran again. Above the arc, not on it: at phone
						     width the label is as wide as the arc and hid all but its tips. -->
						ULTRON sent it back · {ordinal(view.replans + 1)} try
					</span>
				</div>
			{/if}

			{#each view.stages as s, i (s.name)}
				{@const look = looks[i]}
				{@const reached = cascade || i <= shown}
				<div class="relative flex flex-col items-start" role="listitem">
					{#if i < view.stages.length - 1}
						<span class="wire w-{wires[i]}" class:go={i === travelling} aria-hidden="true">
							<span class="base"></span>
							<span class="fill"></span>
							<span class="light"></span>
						</span>
					{/if}

					<!-- -mx-1 px-1: the focus ring gets room while the node stays on
					     the column's edge. Always a button, enabled once the run is
					     over: switching the element rebuilt every node as the run
					     finished and replayed their closing mid-release. -->
					<button
						type="button"
						disabled={!done || s.state === 'skipped'}
						on:click={() => openStage(s.name)}
						class="group -mx-1 flex flex-col items-start rounded-lg px-1 text-left outline-none focus-visible:ring-1 focus-visible:ring-gray-400 disabled:cursor-default"
						aria-label="{s.name}{s.runs > 1 ? `, ran ${s.runs} times` : ''}{reached && s.time
							? `, ${s.time}`
							: ''}{reached && s.note ? `, ${s.note}` : ''}"
					>
						<!-- Hover darkens a finished node's ring rather than growing it. -->
						<span class="node flex size-3.5 items-center justify-center" aria-hidden="true">
							<NodeGlyph kind={look} {motion} bloom={landings[i]} />
						</span>
						<span
							class="mt-2 text-[10.5px] font-medium tracking-[0.08em] {LABEL[look]} transition-colors duration-700"
						>
							<span class="name" class:live-name={look === 'active'} style="--i: {i}"
								>{s.name === 'You' ? 'YOU' : s.name}</span
							>{#if s.runs > 1}<span class="ml-1 font-normal tracking-normal opacity-70">×{s.runs}</span
								>{/if}
						</span>
						<!-- Time and note on their own lines: on a phone a column is ~70px,
						     and "3.7s · reviewing" broke as "3.7s ·" over a stray word.
						     Faded in dark mode only: at 75% on white it measured 3.35:1, under
						     AA for text this small; full strength is 5.3:1. -->
						<span class="text-[10.5px] tabular-nums leading-tight {LABEL[look]} dark:opacity-75">
							{#if reached}
								<!-- Your time is waiting, not work: said so once the decision is in.
								     Each line settles in as the stage is reached. -->
								{#if s.time}<span
										class="block"
										in:fly={{ y: motion ? 3 : 0, duration: motion ? 500 : 0, opacity: 0 }}
										>{s.name === 'You' && (s.state === 'released' || s.state === 'withheld')
											? `waited ${s.time}`
											: s.time}</span
									>{/if}
								{#if s.note}<span
										class="block"
										in:fly={{ y: motion ? 3 : 0, duration: motion ? 500 : 0, delay: motion ? 80 : 0, opacity: 0 }}
										>{s.note}</span
									>{/if}
							{/if}
							{#if !reached || (!s.time && !s.note)}&nbsp;{/if}
						</span>
					</button>
				</div>
			{/each}
		</div>
	</div>
{/if}

<style>
	.rail {
		--wire: var(--color-gray-300, #cdcdcd);
		--charged: var(--color-gray-400, #b4b4b4);
		--held: #fbbf24; /* amber-400: a run cut off */
		--released: var(--color-gray-900, #1c1c1c); /* your decision, either way */
		--name: var(--color-gray-600, #676767);
		--vt: #a78bfa; /* violet-400: the light's tail */
		--vh: #7c3aed; /* violet-600: its head */
		--glow: rgba(124, 58, 237, 0.26);
	}
	:global(.dark) .rail {
		--wire: var(--color-gray-700, #525252);
		--charged: var(--color-gray-600, #676767);
		--held: #d97706; /* amber-600 */
		--released: #fff;
		--name: var(--color-gray-300, #cdcdcd);
		--vt: #8b5cf6;
		--vh: #ddd6fe;
		--glow: rgba(167, 139, 250, 0.36);
	}

	/* A wire: a dashed hairline from one ring to the next, filled once the
	   light has crossed it. */
	.wire {
		position: absolute;
		top: 7px; /* the node's centre */
		left: 18px; /* the 14px node, then a gap */
		right: 4px; /* a gap before the next node, on the next column's edge */
		height: 0;
	}
	.wire > span {
		position: absolute;
		left: 0;
	}
	.base {
		right: 0;
		top: -0.5px;
		border-top: 1px dashed var(--wire);
	}
	.fill {
		right: 0;
		top: -0.5px;
		height: 1px;
		background: var(--charged);
		transform: scaleX(0);
		transform-origin: left center;
		transition: background-color 800ms ease;
	}
	.w-done .fill,
	.w-held .fill,
	.w-released .fill {
		transform: none;
	}
	.w-held .fill {
		background: var(--held);
	}
	.w-released .fill {
		background: var(--released);
	}

	/* The light: a soft violet streak with a bright head. It fades in as it
	   leaves, glides with a long ease into the next node, stops short of it,
	   and fades there as that node starts. The fill follows just behind. */
	.light {
		top: -0.75px;
		width: 26px;
		height: 1.5px;
		border-radius: 2px;
		opacity: 0;
		background: linear-gradient(90deg, transparent, var(--vt) 55%, var(--vh));
		box-shadow: 0 0 4px var(--glow);
		pointer-events: none;
	}
	/* The head: a round point, a touch brighter than the streak. */
	.light::after {
		content: '';
		position: absolute;
		right: -2px;
		top: -1.5px;
		width: 4.5px;
		height: 4.5px;
		border-radius: 50%;
		background: var(--vh);
		box-shadow: 0 0 3px var(--glow);
	}
	.go .light {
		animation:
			light-glide 1900ms cubic-bezier(0.45, 0, 0.2, 1) both,
			light-fade 2450ms linear both;
	}
	/* The wire fills behind the light still faintly violet, and cools to grey
	   as the light fades into the next node. */
	.go .fill {
		animation:
			wire-fill 1900ms cubic-bezier(0.45, 0, 0.2, 1) both,
			wire-cool 2450ms ease both;
	}

	/* Hover on a finished run: the node's ring darkens to ink. */
	.group:enabled:hover .node :global(.node-glyph) {
		--done: var(--color-gray-900, #1c1c1c);
	}
	:global(.dark) .group:enabled:hover .node :global(.node-glyph) {
		--done: #fff;
	}
	.group:enabled:hover .name {
		color: var(--color-gray-900, #1c1c1c);
	}
	:global(.dark) .group:enabled:hover .name {
		color: #fff;
	}
	.name {
		transition: color 300ms ease;
	}

	/* The working stage's name: now and then a soft violet light glides
	   across it, once, then rests. The gradient is three times the name's
	   width and moves from one end to the other, so the band starts and ends
	   just off the letters and always crosses at the same unhurried pace. */
	.live-name {
		background: linear-gradient(
			90deg,
			var(--name) 0%,
			var(--name) 38%,
			var(--vt) 46%,
			var(--vh) 50%,
			var(--vt) 54%,
			var(--name) 62%,
			var(--name) 100%
		);
		background-size: 300% 100%;
		background-position: 100% 0;
		-webkit-background-clip: text;
		background-clip: text;
		-webkit-text-fill-color: transparent;
		animation: name-light 3.8s cubic-bezier(0.37, 0, 0.63, 1) 400ms infinite;
	}
	/* Released: once the tick is in, one light crosses the names, left to
	   right, each a little after the last. */
	.sweeping .name {
		background: linear-gradient(
			90deg,
			currentColor 0%,
			currentColor 38%,
			var(--vt) 46%,
			var(--vh) 50%,
			var(--vt) 54%,
			currentColor 62%,
			currentColor 100%
		);
		background-size: 300% 100%;
		background-position: 100% 0;
		-webkit-background-clip: text;
		background-clip: text;
		-webkit-text-fill-color: transparent;
		animation: name-sweep 2.8s cubic-bezier(0.37, 0, 0.63, 1) calc(1800ms + var(--i) * 220ms) both;
	}

	/* The arc draws itself in from ULTRON's side, then the spark rides it back. */
	.replan {
		animation: arc-draw 520ms cubic-bezier(0.4, 0, 0.2, 1) backwards;
	}
	.arc-spark {
		stroke-dashoffset: 10;
		animation: arc-spark 900ms 380ms cubic-bezier(0.45, 0, 0.3, 1) both;
	}

	@keyframes light-glide {
		from {
			left: 0;
		}
		to {
			left: calc(100% - 24px);
		}
	}
	@keyframes light-fade {
		0% {
			opacity: 0;
		}
		24%,
		77.5% {
			opacity: 1;
		}
		100% {
			opacity: 0;
		}
	}
	@keyframes wire-fill {
		from {
			transform: scaleX(0);
		}
		to {
			transform: scaleX(1);
		}
	}
	@keyframes wire-cool {
		0%,
		70% {
			background-color: color-mix(in srgb, var(--vt) 70%, var(--charged));
		}
		100% {
			background-color: var(--charged);
		}
	}
	@keyframes name-light {
		0% {
			background-position: 100% 0;
		}
		63%,
		100% {
			background-position: 0% 0;
		}
	}
	@keyframes name-sweep {
		from {
			background-position: 100% 0;
		}
		to {
			background-position: 0% 0;
		}
	}
	@keyframes arc-draw {
		from {
			clip-path: inset(0 0 0 100%);
		}
		to {
			clip-path: inset(0 0 0 0);
		}
	}
	@keyframes arc-spark {
		from {
			stroke-dashoffset: 10;
			opacity: 1;
		}
		85% {
			opacity: 1;
		}
		to {
			stroke-dashoffset: -100;
			opacity: 0;
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.light,
		.fill,
		.name,
		.live-name,
		.replan,
		.arc-spark {
			animation: none !important;
		}
		.arc-spark {
			opacity: 0;
		}
	}
</style>
