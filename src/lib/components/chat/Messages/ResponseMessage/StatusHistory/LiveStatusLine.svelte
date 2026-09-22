<script context="module">
	/*
	 * Lines in each agent's voice, shown at random while its stage runs.
	 * Every line has to stay true for any kind of task, so each one paraphrases
	 * what that agent is actually instructed to do (see the *_SYSTEM prompts in
	 * 4ce/functions/orchestrator.py) and none names a source, a number or a
	 * check the run may not have. Specifics come from the orchestrator instead,
	 * as `facts` on the status, because only it knows what is really happening.
	 */
	const LINES = {
		TONY: [
			'Reading your request…',
			'Working out what kind of job this is…',
			'Picking the right model for it…',
			'Lining up the crew…'
		],
		FRIDAY: [
			"Working out what's actually being asked…",
			'Separating fact from assumption…',
			'Working only from what it has been given…',
			'Labelling every assumption…',
			'Checking whether the evidence is enough…',
			'Weighing the details…'
		],
		JARVIS: [
			'Drafting the deliverable…',
			"Turning FRIDAY's analysis into an answer…",
			'Giving it a proper structure…',
			'Choosing the right words…',
			'Putting it all together…'
		],
		ULTRON: [
			'Looking for unsupported claims…',
			'Checking for missing steps…',
			'Hunting for arithmetic slips…',
			'Watching for made-up detail…',
			'Trying to break it…',
			"Playing devil's advocate…"
		],
		REPLAN: [
			"Taking ULTRON's objections on board…",
			'Sending it back through the chain…',
			'Rethinking the approach…'
		],
		YOU: [
			'Waiting for your sign-off…',
			'Nothing is released until you approve it…',
			'Review the draft below…'
		]
	};

	const VOICE = {
		tony: 'TONY',
		tony_plan: 'TONY',
		router: 'TONY',
		friday: 'FRIDAY',
		jarvis: 'JARVIS',
		ultron: 'ULTRON',
		tony_replan: 'REPLAN',
		approval: 'YOU'
	};

	/* The 4CE statuses this line handles; anything else stays with upstream's
	   StatusItem (web search, knowledge search and so on). */
	export const FOURCE_ACTIONS = new Set([
		...Object.keys(VOICE),
		'chat',
		'tool',
		'done',
		'stopped',
		'error'
	]);
</script>

<script>
	/*
	 * LiveStatusLine - the one-line status under the stage rail, alive while a
	 * stage runs: it opens on the orchestrator's own words for the stage, then
	 * rolls through lines in that agent's voice, with one of the run's real
	 * details every third line. Nothing is invented and nothing is hidden: the
	 * factual status leads every stage, and the full history is one click away.
	 */
	import { onDestroy } from 'svelte';
	import { fly } from 'svelte/transition';

	export let status = null;

	const EVERY = 2600; // ms each line stays up

	let line = '';
	let serial = 0; // bumps on every change, so the roll-up animates each one
	let step = 0;
	let factAt = 0;
	let timer = null;

	const reduced =
		typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

	$: live = status?.done === false;

	function show(text) {
		if (!text || text === line) return;
		line = text;
		serial += 1;
	}

	function next() {
		step += 1;
		const facts = (status?.facts ?? []).filter(Boolean);
		const pool = LINES[VOICE[status?.action]] ?? [];
		// Line, fact, line, line, fact, ... - the voice carries it, the facts
		// keep it honest.
		if (facts.length && (step % 3 === 2 || !pool.length)) {
			show(facts[factAt++ % facts.length]);
		} else if (pool.length) {
			const fresh = pool.filter((l) => l !== line);
			show(fresh[Math.floor(Math.random() * fresh.length)]);
		}
	}

	/* A new status (a new stage, or new words for this one) starts over on the
	   orchestrator's own description. A function called with `sig` alone: a
	   reactive block depends only on what it names, so the line it writes
	   cannot re-trigger it. */
	function restart() {
		clearInterval(timer);
		timer = null;
		step = 0;
		factAt = 0;
		show(status?.description ?? '');
		if (status?.done === false && (LINES[VOICE[status?.action]] || status?.facts?.length)) {
			timer = setInterval(next, EVERY);
		}
	}

	$: sig = `${status?.action}|${status?.description}|${status?.done}`;
	$: restart(sig);

	onDestroy(() => clearInterval(timer));
</script>

<!-- Screen readers get the factual status when it changes, not a new line
     every 2.6 seconds; the rolling lines are for the eye only. -->
<span class="sr-only" aria-live="polite">{status?.description ?? ''}</span>

<!-- Both lines share one grid cell while they cross, so the box keeps its
     height and nothing below it moves. -->
<div class="grid overflow-hidden py-0.5" aria-hidden="true">
	{#key serial}
		<div
			class="[grid-area:1/1] text-[0.9375rem] line-clamp-1 text-left {live
				? 'shimmer'
				: 'text-gray-500 dark:text-gray-500'}"
			in:fly={{ y: reduced ? 0 : 10, duration: reduced ? 0 : 340, opacity: 0 }}
			out:fly={{ y: reduced ? 0 : -10, duration: reduced ? 0 : 260, opacity: 0 }}
		>
			{line}
		</div>
	{/key}
</div>
