<script>
	/*
	 * StageRail - the 4CE agent chain as a node path at the top of each answer:
	 *   TONY ● ╌╌ ● FRIDAY ╌╌ ● JARVIS ╌╌ ● ULTRON ╌╌ ○ You
	 * One dot for every stage, the human gate included: a ring while it waits
	 * on you, filled with a tick when you release and a dash when you
	 * withhold - one shape and ink only, so the rail ends as it began. The wires are short cut lines that
	 * carry energy cut by cut:
	 * - after the live agent, pulses run toward the next node - indeterminate
	 *   motion, never a fake percentage;
	 * - when a stage hands over, a spark charges the wire into the next node,
	 *   and that node lands as the spark reaches it;
	 * - the gate's wire charges in ink once you decide, either way;
	 * - a finished chat charges its chain once, left to right, when it opens.
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
	 * Direct replies ("hi") never reach the chain, so they get no rail. There
	 * is no orb here on purpose: the avatar carries the one orb.
	 */
	import { onDestroy } from 'svelte';

	export let statusHistory = [];
	export let done = false;

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

	/* A rail that mounts already finished (an opened chat) charges its chain
	   once, left to right: wire i starts STEP ms after wire i - 1, and node j
	   lands as the charge reaches it. A live run animates each handover as it
	   happens instead, so it never waits on a cascade. */
	const cascade = done;
	const STEP = 120;
	const CHARGE = 380;
	const wireDelay = (i) => (cascade ? 80 + i * STEP : 0);
	const nodeDelay = (j) => (cascade && j > 0 ? 80 + (j - 1) * STEP + CHARGE - 60 : 0);

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
			return { name, state, time: known ? fmt(secs) : null, note, runs };
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
	onDestroy(() => {
		timer && clearInterval(timer);
		clearTimeout(sweepTimer);
	});

	/* One-shot moments of a live run. A replan fires a spark back along the arc
	   to FRIDAY - its own event, because on a real run FRIDAY starts again
	   within milliseconds of the replan, so there is no replan stage long
	   enough to animate. A release sends one green charge down the whole rail. */
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
	function syncSweep(stages) {
		if (swept || stages[stages.length - 1]?.state !== 'released') return;
		swept = true;
		sweeping = true;
		sweepTimer = setTimeout(() => (sweeping = false), 1400);
	}
	$: syncSweep(view.stages);
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

	/* Node and label colour per state. */
	const DOT = {
		done: 'bg-gray-400 dark:bg-gray-500',
		active: 'bg-gray-900 dark:bg-white',
		pending: 'border border-gray-300 dark:border-gray-600',
		requeued: 'border border-gray-400 dark:border-gray-500',
		skipped: 'border border-dashed border-gray-200 dark:border-gray-700',
		fail: 'bg-amber-500',
		withheld: 'bg-gray-900 dark:bg-white',
		interrupted: 'bg-amber-500',
		released: 'bg-gray-900 dark:bg-white'
	};
	const LABEL = {
		done: 'text-gray-600 dark:text-gray-300',
		active: 'text-gray-900 dark:text-white',
		pending: 'text-gray-400 dark:text-gray-500',
		requeued: 'text-gray-500 dark:text-gray-400',
		skipped: 'text-gray-300 dark:text-gray-600',
		fail: 'text-amber-700 dark:text-amber-300',
		withheld: 'text-gray-600 dark:text-gray-300',
		interrupted: 'text-amber-700 dark:text-amber-300',
		released: 'text-gray-900 dark:text-white'
	};

	/* The wire leaving stage i, toward stage i + 1. */
	function wire(stages, i) {
		const from = stages[i];
		const to = stages[i + 1];
		if (from.state === 'active') return 'flow';
		if (to.name === 'You') {
			// Your decision, either way, charges the wire in ink; only a run cut
			// off before you decided stays amber.
			if (to.state === 'released' || to.state === 'withheld') return 'released';
			if (to.state === 'interrupted') return 'held';
		}
		if (['pending', 'skipped', 'requeued'].includes(to.state)) return 'future';
		return 'done';
	}
	$: wires = view.stages.slice(0, -1).map((_, i) => wire(view.stages, i));
	// Kinds whose wire is charged; each has its own animation name, so a wire
	// that turns from charged to amber or green charges again in its colour.
	const CHARGED = new Set(['done', 'held', 'released']);
</script>

{#if view.inChain}
	<!-- Flush with the text column: TONY's dot sits on the same left edge as
	     the model name and the answer, and each label starts under its dot.
	     The four agents share the width; YOU takes what its label needs, so
	     the gate always ends the rail. -->
	<div
		bind:this={root}
		class="rail relative mb-3 w-full max-w-[34rem] {view.replans > 0 ? 'pt-9' : 'pt-2.5'}"
		class:sweeping
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
				     FRIDAY's column to ULTRON's, so it meets both dots at any width.
				     While the run is live its cuts travel back toward FRIDAY. -->
				<div
					class="pointer-events-none absolute col-start-2 col-end-4 row-start-1 -top-[22px] left-[5px] right-[-5px] h-[22px]"
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
				<div class="relative flex flex-col items-start" role="listitem">
					{#if i < view.stages.length - 1}
						<span
							class="wire w-{wires[i]}"
							class:charged={CHARGED.has(wires[i])}
							style="--d: {wireDelay(i)}ms"
							aria-hidden="true"
						>
							<span class="cuts">
								<span class="fill"></span>
								<span class="spark"></span>
								<span class="packet"></span>
								<span class="sweep" style="--sd: {i * 110}ms"></span>
							</span>
						</span>
					{/if}

					<!-- -mx-1 px-1: the focus ring gets room while the dot stays on the
					     column's edge. -->
					<svelte:element
						this={done && s.state !== 'skipped' ? 'button' : 'span'}
						type={done && s.state !== 'skipped' ? 'button' : undefined}
						role={done && s.state !== 'skipped' ? 'button' : undefined}
						on:click={() => done && s.state !== 'skipped' && openStage(s.name)}
						class="group -mx-1 flex flex-col items-start rounded-md px-1 text-left outline-none focus-visible:ring-1 focus-visible:ring-gray-400"
						aria-label="{s.name}{s.runs > 1 ? `, ran ${s.runs} times` : ''}{s.time
							? `, ${s.time}`
							: ''}{s.note ? `, ${s.note}` : ''}"
					>
						<!-- `go` / `settle` land a node when the charge reaches it live;
						     separate names so active -> outcome lands again. -->
						<span
							class="node relative flex size-2.5 items-center justify-center"
							class:go={!cascade && s.state === 'active'}
							class:settle={!cascade && (s.state === 'released' || s.state === 'withheld')}
							class:cascade-in={cascade && s.state !== 'skipped'}
							style="--nd: {nodeDelay(i)}ms"
							aria-hidden="true"
						>
							{#if s.state === 'active'}
								<!-- A soft glow that beats with the pulses leaving along the
								     wire (same 1.1s period, same start), in place of the
								     generic ping ring. -->
								<span class="halo absolute inset-0 rounded-full"></span>
							{/if}
							{#if s.state === 'released'}
								<span class="burst rounded-full"></span>
							{/if}
							{#if s.name === 'You' && (s.state === 'released' || s.state === 'withheld')}
								<!-- Your decision: the gate fills, with a tick or a dash. -->
								<span
									class="relative inline-flex size-3 shrink-0 items-center justify-center rounded-full {DOT[
										s.state
									]} transition-all duration-300 {done ? 'group-hover:scale-125' : ''}"
								>
									<svg
										class="size-2 text-white dark:text-gray-900"
										viewBox="0 0 8 8"
										fill="none"
										stroke="currentColor"
										stroke-width="1.4"
										stroke-linecap="round"
										stroke-linejoin="round"
										><path d={s.state === 'released' ? 'M1.6 4.2l1.6 1.6 3.2-3.5' : 'M2 4h4'} /></svg
									>
								</span>
							{:else}
								<span
									class="relative inline-flex size-2.5 rounded-full {s.name === 'You' &&
									s.state === 'active'
										? 'border-[1.5px] border-gray-900 bg-white dark:border-white dark:bg-gray-900'
										: DOT[s.state]} transition-all duration-300 {done && s.state !== 'skipped'
										? 'group-hover:scale-125'
										: ''}"
								></span>
							{/if}
						</span>
						<span
							class="mt-2 text-[10.5px] font-medium tracking-[0.08em] {LABEL[s.state]} transition-colors duration-500"
						>
							{s.name === 'You' ? 'YOU' : s.name}{#if s.runs > 1}<span
									class="ml-1 font-normal tracking-normal opacity-70">×{s.runs}</span
								>{/if}
						</span>
						<!-- Time and note on their own lines: on a phone a column is ~70px,
						     and "3.7s · reviewing" broke as "3.7s ·" over a stray word.
						     Faded in dark mode only: at 75% on white it measured 3.35:1, under
						     AA for text this small; full strength is 5.3:1. -->
						<span class="text-[10.5px] tabular-nums leading-tight {LABEL[s.state]} dark:opacity-75">
							{#if s.time}<span class="block">{s.time}</span>{/if}
							{#if s.note}<span class="block">{s.note}</span>{/if}
							{#if !s.time && !s.note}&nbsp;{/if}
						</span>
					</svelte:element>
				</div>
			{/each}
		</div>
	</div>
{/if}

<style>
	.rail {
		--ink: var(--color-gray-900, #1c1c1c);
		--cut: var(--color-gray-200, #e5e5e5);
		--charged: var(--color-gray-400, #b4b4b4);
		--held: #fbbf24; /* amber-400: a run cut off */
		--released: var(--ink); /* your decision, either way */
		--glow: none;
	}
	:global(.dark) .rail {
		--ink: #fff;
		--cut: var(--color-gray-800, #3b3b3b);
		--charged: var(--color-gray-600, #6a6a6a);
		--held: #d97706; /* amber-600 */
		--released: var(--ink);
		--glow: drop-shadow(0 0 1px rgba(255, 255, 255, 0.45));
	}

	/* A wire is a row of short cuts - 4px on, 3px off. The mask on .cuts
	   applies to every layer inside it (resting colour, charge, spark,
	   pulses), so anything moving along the wire moves cut by cut. */
	.wire {
		position: absolute;
		top: 4px;
		left: 15px; /* the 10px dot, then a 5px gap */
		right: 5px; /* a 5px gap before the next dot, on the next column's edge */
		height: 2px;
	}
	.cuts {
		position: absolute;
		inset: 0;
		overflow: hidden;
		background: var(--cut);
		-webkit-mask-image: repeating-linear-gradient(90deg, #000 0 4px, transparent 4px 7px);
		mask-image: repeating-linear-gradient(90deg, #000 0 4px, transparent 4px 7px);
	}
	.cuts > span {
		position: absolute;
		top: 0;
		bottom: 0;
		left: 0;
	}

	/* Resting colour of the wire. */
	.fill {
		right: 0;
		transform-origin: left center;
	}
	.w-done .fill {
		background: var(--charged);
	}
	.w-held .fill {
		background: var(--held);
	}
	.w-released .fill {
		background: var(--released);
	}
	.w-flow .fill {
		background: var(--ink);
		opacity: 0.16;
	}

	/* The handover: the wire charges from the left while a spark rides the
	   front of the charge into the next node. */
	.charged .fill {
		animation: charge var(--charge, 380ms) var(--d) cubic-bezier(0.4, 0, 0.2, 1) backwards;
	}
	.w-held .fill {
		animation-name: charge-held;
	}
	.w-released .fill {
		animation-name: charge-released;
	}
	.spark {
		width: 18px;
		opacity: 0;
		background: linear-gradient(90deg, transparent, var(--ink));
	}
	.charged .spark {
		animation: spark 380ms var(--d) cubic-bezier(0.4, 0, 0.2, 1) backwards;
	}
	.w-held .spark {
		animation-name: spark-held;
	}
	.w-released .spark {
		animation-name: spark-released;
	}

	/* The live stage: pulses of energy leave it toward the next node, lit
	   cut by cut, starting once the node itself has landed. */
	.w-flow {
		filter: var(--glow);
	}
	.packet {
		display: none;
		width: 40%;
		background: linear-gradient(90deg, transparent, var(--ink) 80%, transparent);
	}
	.w-flow .packet {
		display: block;
		animation: packet 1.1s 300ms linear infinite backwards;
	}

	/* A node lands - a small overshoot - as the charge reaches it. */
	.node.go {
		animation: land-live 360ms 300ms cubic-bezier(0.34, 1.56, 0.64, 1) backwards;
	}
	.node.settle {
		animation: land-outcome 360ms 300ms cubic-bezier(0.34, 1.56, 0.64, 1) backwards;
	}
	.node.cascade-in {
		animation: land-live 320ms var(--nd) cubic-bezier(0.34, 1.56, 0.64, 1) backwards;
	}
	/* Released: one soft ring off the gate, once. */
	.burst {
		position: absolute;
		inset: 0;
		border: 1px solid var(--released);
		opacity: 0;
		pointer-events: none;
		animation: burst 900ms calc(var(--nd) + 420ms) ease-out backwards;
	}

	/* The arc draws itself in from ULTRON's side, then the spark rides it back. */
	.replan {
		animation: arc-draw 520ms cubic-bezier(0.4, 0, 0.2, 1) backwards;
	}
	.arc-spark {
		stroke-dashoffset: 10;
		animation: arc-spark 900ms 380ms cubic-bezier(0.45, 0, 0.3, 1) both;
	}

	/* The live node's glow, in time with its wire's pulses. */
	.rail {
		--halo: rgba(30, 27, 51, 0.3);
	}
	:global(.dark) .rail {
		--halo: rgba(255, 255, 255, 0.34);
	}
	.halo {
		animation: halo 1.1s 300ms cubic-bezier(0.2, 0.6, 0.35, 1) infinite backwards;
	}

	/* Release: one green charge down the whole rail, wire after wire. */
	.sweep {
		width: 22px;
		opacity: 0;
		background: linear-gradient(90deg, transparent, var(--released));
	}
	.sweeping .sweep {
		animation: sweep 460ms var(--sd) cubic-bezier(0.4, 0, 0.2, 1) backwards;
	}

	@keyframes charge {
		from {
			transform: scaleX(0);
		}
	}
	@keyframes charge-held {
		from {
			transform: scaleX(0);
		}
	}
	@keyframes charge-released {
		from {
			transform: scaleX(0);
		}
	}
	@keyframes spark {
		from {
			left: -18px;
			opacity: 1;
		}
		85% {
			opacity: 1;
		}
		to {
			left: 100%;
			opacity: 0;
		}
	}
	@keyframes spark-held {
		from {
			left: -18px;
			opacity: 1;
		}
		85% {
			opacity: 1;
		}
		to {
			left: 100%;
			opacity: 0;
		}
	}
	@keyframes spark-released {
		from {
			left: -18px;
			opacity: 1;
		}
		85% {
			opacity: 1;
		}
		to {
			left: 100%;
			opacity: 0;
		}
	}
	@keyframes packet {
		from {
			transform: translateX(-100%);
		}
		to {
			transform: translateX(250%);
		}
	}
	@keyframes land-live {
		from {
			scale: 0.4;
			opacity: 0.35;
		}
	}
	@keyframes land-outcome {
		from {
			scale: 0.4;
			opacity: 0.35;
		}
	}
	@keyframes burst {
		from {
			opacity: 0.9;
			scale: 1;
		}
		to {
			opacity: 0;
			scale: 3;
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
	@keyframes halo {
		from {
			box-shadow: 0 0 0 0 var(--halo);
		}
		to {
			box-shadow: 0 0 0 7px transparent;
		}
	}
	@keyframes sweep {
		from {
			left: -22px;
			opacity: 1;
		}
		85% {
			opacity: 1;
		}
		to {
			left: 100%;
			opacity: 0;
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.fill,
		.spark,
		.packet,
		.node,
		.burst,
		.replan,
		.arc-spark,
		.halo,
		.sweep {
			animation: none !important;
		}
		.arc-spark {
			opacity: 0;
		}
		/* Still say which wire is live, without motion. */
		.w-flow .fill {
			opacity: 0.45;
		}
	}
</style>
