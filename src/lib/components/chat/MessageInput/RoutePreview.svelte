<script context="module">
	/*
	 * Where a request will go, worked out as you type, before it is sent.
	 * The same keywords TONY classifies by (4ce/functions/orchestrator.py:
	 * GREETINGS, COURTESIES, META_QUESTIONS, CODE_SIGNALS, DOCUMENT_SIGNALS,
	 * CALC_SIGNALS, AUDIT_SIGNALS and the readings pattern), so the guess and
	 * the run agree. TONY still decides after sending; this is a preview.
	 */
	const GREETINGS = new Set(
		'afternoon|evening|good afternoon|good day|good evening|good morning|greetings|hello|hey|hi|hiya|hola|howdy|morning|namaste|yo'.split('|')
	);
	const COURTESIES = new Set(
		'again|ah|alright|and|and again|brilliant|bye|carry on|cheers|continue|cool|correct|exactly|excellent|fine|go on|good night|goodbye|got it|great|hm|hmm|i see|indeed|k|lovely|makes sense|next|nice|no|noted|oh|ok|okay|once more|one more|perfect|right|same again|see you|so|sure|ta|test|testing|thank you|thanks|thankyou|understood|wonderful|yes'.split('|')
	);
	const META = 'who are you|what are you|what can you do|what do you do|how do you work|what is 4ce|who made you|introduce yourself|what models do you|which models do you|are you online|are you there'.split('|');
	const CODE = 'code|script|program|function|debug|compile|refactor|python|javascript|sql|algorithm|unit test|traceback'.split('|');
	const DOCUMENT = 'report|inspection|sop|manual|approval note|summarise|summarize|findings|drawing|correspondence|note sheet|tender|specification|procedure|audit'.split('|');
	const AUDIT = 'prove nothing leaves|leaves the premises|leave the premises|sovereignty|sovereign|audit the running|audit the configuration|external call|air gap|air-gapped|offline mode|telemetry|data leaving|phone home'.split('|');
	const READINGS = /\d+(?:\.\d+)?\s*(?:drops?\s*(?:per\s*minute|\/\s*min|pm)|mm\s*\/\s*s|mm|microns?|µm|um|bar(?:\s*g)?|kpa|mpa|psi|°\s*c|deg\s*c|\bc\b|rpm|hz|%|litres?\s*\/\s*min|l\s*\/\s*min|m3\s*\/\s*h)\b/i;

	function smallTalk(prompt) {
		const text = prompt.toLowerCase().replace(/[^a-z0-9\s]/g, ' ').split(/\s+/).filter(Boolean);
		if (!text.length || text.length > 8) return false;
		const joined = text.join(' ');
		if (GREETINGS.has(joined) || COURTESIES.has(joined)) return true;
		if (GREETINGS.has(text[0]) && text.length <= 5) return true;
		return META.some((m) => joined.includes(m));
	}

	export function routeOf(prompt, { image = false, knowledge = 'your documents' } = {}) {
		const t = (prompt ?? '').trim();
		if (!t) return null;
		const lowered = t.toLowerCase();
		const has = (list) => list.some((w) => lowered.includes(w));
		const audit = has(AUDIT);
		const readings = READINGS.test(t);
		let kind;
		if (image) kind = 'vision';
		else if (smallTalk(t)) kind = 'chat';
		else if (has(CODE)) kind = 'code';
		else if (has(DOCUMENT)) kind = 'document';
		else kind = 'analysis';

		if (kind === 'chat') return { kind, agents: [1, 0, 0, 0, 0], label: 'Direct reply', steps: ['no agents', 'no sign-off'] };
		const steps = [];
		if (audit) steps.push('4CE inspects its own running setup');
		if (kind === 'code') steps.push('JARVIS writes it and runs it in the sealed sandbox');
		else if (kind === 'vision') steps.push('FRIDAY reads the page', 'the SOP limits are checked by rule');
		else {
			steps.push(`FRIDAY reads ${knowledge}`);
			if (readings) steps.push('the SOP limits are checked by rule');
		}
		steps.push('ULTRON checks', 'you sign off');
		const label = audit
			? 'Sovereignty audit'
			: { code: 'Code', vision: 'Reading the image', document: 'Document task', analysis: 'Analysis' }[kind];
		return { kind, agents: [1, 1, 1, 1, 1], label, steps };
	}
</script>

<script>
	/*
	 * RoutePreview - one quiet line under the message box: a small rail with
	 * the agents the request will reach, and where it goes, in words. It
	 * follows what you type (after a short pause), crosses over when the
	 * route changes, and stays out of the way when there is nothing to show.
	 */
	import { onDestroy } from 'svelte';
	import { fade } from 'svelte/transition';

	export let prompt = '';
	export let files = [];
	export let knowledge = 'your documents';

	const NAMES = ['TONY', 'FRIDAY', 'JARVIS', 'ULTRON', 'YOU'];

	let route = null;
	let timer = 0;
	$: image = (files ?? []).some((f) => f?.type === 'image');
	$: schedule(prompt, image, knowledge);

	function schedule(text, img, kb) {
		clearTimeout(timer);
		// Cleared at once; shown after a short pause, so it doesn't flicker
		// with every key.
		if (!(text ?? '').trim()) {
			route = null;
			return;
		}
		timer = setTimeout(() => (route = routeOf(text, { image: img, knowledge: kb })), 220);
	}
	onDestroy(() => clearTimeout(timer));

	$: key = route ? `${route.label}|${route.steps.join('|')}` : '';
</script>

<div class="route-line" class:on={!!route} aria-live="polite">
	{#if route}
		<span class="flex shrink-0 items-center" aria-hidden="true">
			{#each route.agents as on, i}
				{#if i}<span class="wire" class:lit={on && route.agents[i - 1]}></span>{/if}
				<span class="node" class:lit={on} class:you={i === 4} title={NAMES[i]} style="--i: {i}"></span>
			{/each}
		</span>
		<span class="grid min-w-0 flex-1">
			{#key key}
				<span class="[grid-area:1/1] truncate" in:fade={{ duration: 220, delay: 90 }} out:fade={{ duration: 140 }}>
					<span class="font-medium text-gray-800 dark:text-gray-200">{route.label}</span
					>{#each route.steps as step}<span class="sep" aria-hidden="true">·</span><span class="sr-only">, </span><span
							>{step}</span
						>{/each}
				</span>
			{/key}
		</span>
	{/if}
</div>

<style>
	.route-line {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		min-height: 0;
		max-height: 0;
		overflow: hidden;
		padding: 0 0.9rem;
		font-size: 12.5px;
		color: var(--color-gray-600, #676767);
		opacity: 0;
		transform: translateY(-3px);
		transition:
			max-height 320ms cubic-bezier(0.22, 1, 0.36, 1),
			margin 320ms cubic-bezier(0.22, 1, 0.36, 1),
			opacity 240ms ease,
			transform 400ms cubic-bezier(0.22, 1, 0.36, 1);
	}
	.route-line.on {
		max-height: 2rem;
		margin-top: 0.45rem;
		opacity: 1;
		transform: none;
	}
	:global(.dark) .route-line {
		color: var(--color-gray-400, #b4b4b4);
	}
	/* The rail in miniature: rings for the agents it reaches, dashed for the
	   ones it passes by, your gate in violet. */
	.node {
		display: block;
		width: 9px;
		height: 9px;
		border-radius: 9999px;
		box-sizing: border-box;
		border: 1px dashed var(--color-gray-300, #cdcdcd);
		transition:
			border-color 400ms ease calc(var(--i) * 45ms),
			background 400ms ease calc(var(--i) * 45ms);
	}
	.node.lit {
		border: 1.25px solid var(--color-gray-700, #525252);
		background: radial-gradient(circle, var(--color-gray-700, #525252) 0 1.5px, transparent 2px);
	}
	.node.you.lit {
		border-color: #7c3aed;
		background: radial-gradient(circle, #7c3aed 0 1.5px, transparent 2px);
	}
	.wire {
		display: block;
		width: 8px;
		border-top: 1px dashed var(--color-gray-300, #cdcdcd);
	}
	.wire.lit {
		border-top: 1px solid var(--color-gray-400, #b4b4b4);
	}
	:global(.dark) .node {
		border-color: var(--color-gray-700, #525252);
	}
	:global(.dark) .node.lit {
		border-color: var(--color-gray-300, #cdcdcd);
		background: radial-gradient(circle, var(--color-gray-300, #cdcdcd) 0 1.5px, transparent 2px);
	}
	:global(.dark) .node.you.lit {
		border-color: #c4b5fd;
		background: radial-gradient(circle, #c4b5fd 0 1.5px, transparent 2px);
	}
	:global(.dark) .wire {
		border-color: var(--color-gray-700, #525252);
	}
	:global(.dark) .wire.lit {
		border-color: var(--color-gray-600, #676767);
	}
	.sep {
		margin: 0 0.45em;
		color: var(--color-gray-400, #b4b4b4);
	}
	:global(.dark) .sep {
		color: var(--color-gray-600, #676767);
	}
	@media (prefers-reduced-motion: reduce) {
		.route-line,
		.node {
			transition: none;
		}
	}
</style>
