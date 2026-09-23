<script context="module">
	/*
	 * A run that stopped, read from the orchestrator's own error text
	 * (`_failure()` in 4ce/functions/orchestrator.py): "**4CE error:**", then
	 * its plain-language fix when it recognised the cause, then "*Detail: ...*"
	 * with what the model server said. Read from the text rather than from a
	 * new field, so chats saved before this card read the same way.
	 */
	const PREFIX = '**4CE error:**';

	const KINDS = [
		{
			kind: 'server',
			match: /isn't reachable|connect call failed|cannot connect to host|connection refused|errno 61|all connection attempts failed|server connection error/i,
			title: "The model server isn't running",
			sub: (who) => `${who} could not reach the local models.`,
			steps: ['Open Bionic.', 'Turn on its server: Developer, then Start Server.', 'Then try again.']
		},
		{
			kind: 'load',
			match: /isn't loaded|model not found|no model|not loaded|does not exist/i,
			title: "A model isn't loaded",
			sub: (who, model) =>
				model ? `${who} was routed to ${model}, which Bionic has not loaded.` : `${who} was routed to a model Bionic has not loaded.`,
			steps: ["Load 4CE's models in Bionic, or run the command below.", 'Then try again.'],
			command: 'python 4ce/preflight.py --fix'
		},
		{
			kind: 'context',
			match: /context window|exceeds the available context|context size|context length|maximum context|too many tokens/i,
			title: 'This request is too long for the model',
			sub: () => "It is longer than the model's context window.",
			steps: [
				'Attach long documents instead of pasting them, so only the passages that matter are sent.',
				'Then try again.'
			]
		},
		{
			kind: 'slow',
			match: /took too long|timed out|timeout/i,
			title: 'The model took too long to answer',
			sub: (who) => `${who} waited, then stopped.`,
			steps: [
				'If answers are slow in general, a model is probably loaded above 8192 context. Run the command below.',
				'Then try again.'
			],
			command: 'python 4ce/preflight.py --fix'
		}
	];

	export function parseRunError(content) {
		const text = (content ?? '').trim();
		if (!text.startsWith(PREFIX)) return null;
		const body = text.slice(PREFIX.length).trim();
		const detailAt = body.search(/\n\s*\n\*Detail:/);
		const advice = detailAt >= 0 ? body.slice(0, detailAt).trim() : '';
		const detail = (detailAt >= 0 ? body.slice(detailAt) : body)
			.trim()
			.replace(/^\*Detail:\s*/, '')
			.replace(/\*$/, '')
			.trim();
		const model = detail.match(/'([^']+)'/)?.[1] ?? '';
		const known = KINDS.find((k) => k.match.test(advice) || k.match.test(detail));
		return { advice, detail, model, known };
	}
</script>

<script>
	/*
	 * RunErrorCard - a stopped run, said plainly: what went wrong, where, the
	 * fix as short steps (a command in its own box with a copy button), a way
	 * to try again, and what the model server actually said, folded away.
	 */
	import { createEventDispatcher } from 'svelte';
	import { fade } from 'svelte/transition';
	import { copyToClipboard } from '$lib/utils';

	export let error;
	/** The agent the run stopped at, from the stage rail. */
	export let who = '';
	export let canRetry = false;

	const dispatch = createEventDispatcher();

	$: agent = who ? (who === 'You' ? '4CE' : who) : '4CE';
	$: known = error?.known ?? null;
	$: title = known?.title ?? 'The run stopped';
	$: sub = known ? known.sub(agent, error.model) : `Something went wrong while ${agent} was working.`;
	$: steps = known?.steps ?? [
		error?.advice || 'Try again. If it happens again, what the model server said is below.'
	];
	$: command = known?.command ?? '';

	let open = false;
	let copied = false;
	let copyTimer;
	let retrying = false;

	const copy = async () => {
		const ok = await copyToClipboard(command);
		if (ok === false) return;
		copied = true;
		clearTimeout(copyTimer);
		copyTimer = setTimeout(() => (copied = false), 1600);
	};

	const retry = () => {
		if (retrying) return;
		retrying = true;
		dispatch('retry');
	};

	const ICONS = {
		server: ['M9 7V3.5M15 7V3.5', 'M7 7h10v3.5a5 5 0 0 1-10 0V7Z', 'M12 15.5V20.5', 'M4 4l16 16'],
		load: ['M20.5 8 12 3.5 3.5 8v8l8.5 4.5 8.5-4.5V8Z', 'M3.5 8 12 12.5 20.5 8', 'M12 12.5v8'],
		context: ['M7 3.5h7l4.5 4.5v12.5H7z', 'M14 3.5V8h4.5', 'M10 12.5h5.5M10 16h5.5'],
		slow: ['M12 3.5a8.5 8.5 0 1 0 0 17 8.5 8.5 0 0 0 0-17Z', 'M12 7.5V12l3 2'],
		other: ['M12 3.5a8.5 8.5 0 1 0 0 17 8.5 8.5 0 0 0 0-17Z', 'M12 8v4.5', 'M12 16v.01']
	};
	$: icon = ICONS[known?.kind ?? 'other'];
</script>

<div
	class="run-error my-1 max-w-[40rem] rounded-2xl border border-gray-100 bg-white px-[18px] pb-3.5 pt-4 dark:border-gray-800 dark:bg-gray-900"
	in:fade={{ duration: 300 }}
>
	<div class="flex items-start gap-3">
		<span
			class="flex size-7 shrink-0 items-center justify-center rounded-[10px] bg-amber-50 text-amber-600 ring-1 ring-inset ring-amber-100 dark:bg-amber-500/10 dark:text-amber-400 dark:ring-amber-500/15"
			aria-hidden="true"
		>
			<svg
				class="size-4"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="1.7"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				{#each icon as d}<path {d} />{/each}
			</svg>
		</span>
		<div class="min-w-0 pt-[3px]">
			<p class="text-[15px] font-medium leading-snug text-gray-900 dark:text-gray-50">{title}</p>
			<p class="mt-0.5 text-[12.5px] leading-snug text-gray-600 dark:text-gray-400">{sub}</p>
		</div>
	</div>

	<ol class="ml-10 mt-3 space-y-1.5">
		{#each steps as step, i}
			<li class="flex gap-2.5 text-[14px] leading-[1.55] text-gray-700 dark:text-gray-300">
				{#if steps.length > 1}
					<span
						class="mt-[3px] flex size-[18px] shrink-0 items-center justify-center rounded-full bg-gray-100 text-[10.5px] font-medium tabular-nums text-gray-600 dark:bg-gray-800 dark:text-gray-300"
						aria-hidden="true">{i + 1}</span
					>
				{/if}
				<span>{step}</span>
			</li>
		{/each}
	</ol>

	{#if command}
		<div
			class="ml-10 mt-2.5 flex items-center gap-2 rounded-xl bg-gray-50 py-1.5 pl-3 pr-1.5 ring-1 ring-inset ring-gray-100 dark:bg-gray-850 dark:ring-gray-800"
		>
			<code class="min-w-0 flex-1 truncate font-mono text-[12.5px] text-gray-800 dark:text-gray-200">{command}</code>
			<button
				type="button"
				class="flex shrink-0 items-center gap-1 rounded-lg px-2 py-1 text-[12px] font-medium text-gray-600 outline-none transition hover:bg-gray-200/70 hover:text-gray-900 focus-visible:ring-2 focus-visible:ring-gray-300 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-white"
				aria-label={copied ? 'Copied' : 'Copy command'}
				on:click={copy}
			>
				<span class="relative size-3.5" aria-hidden="true">
					<svg
						class="absolute inset-0 size-3.5 transition duration-200 {copied ? 'scale-50 opacity-0' : ''}"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.8"
						stroke-linecap="round"
						stroke-linejoin="round"><rect x="8.5" y="8.5" width="11" height="11" rx="2.5" /><path d="M15.5 8.5V6a1.5 1.5 0 0 0-1.5-1.5H6A1.5 1.5 0 0 0 4.5 6v8A1.5 1.5 0 0 0 6 15.5h2.5" /></svg
					>
					<svg
						class="absolute inset-0 size-3.5 text-emerald-600 transition duration-200 dark:text-emerald-400 {copied
							? ''
							: 'scale-50 opacity-0'}"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg
					>
				</span>
				<span class="w-[3.4rem] text-left">{copied ? 'Copied' : 'Copy'}</span>
			</button>
		</div>
	{/if}

	<div class="ml-10 mt-3.5 flex flex-wrap items-center gap-1.5">
		{#if canRetry}
			<button
				type="button"
				class="retry group inline-flex items-center gap-1.5 rounded-full bg-gray-900 px-3.5 py-[7px] text-[13px] font-medium text-white outline-none transition hover:bg-gray-800 focus-visible:ring-2 focus-visible:ring-gray-400 focus-visible:ring-offset-2 disabled:cursor-default dark:bg-white dark:text-gray-900 dark:hover:bg-gray-100 dark:focus-visible:ring-offset-gray-900"
				disabled={retrying}
				on:click={retry}
			>
				<svg
					class="size-3.5 transition-transform duration-500 ease-out group-hover:-rotate-90 {retrying
						? 'animate-spin'
						: ''}"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
					aria-hidden="true"><path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3" /><path d="M19.5 4.5v4h-4" /></svg
				>
				{retrying ? 'Trying again' : 'Try again'}
			</button>
		{/if}
		<button
			type="button"
			class="inline-flex items-center gap-1 rounded-full px-2 py-[7px] text-[12.5px] text-gray-600 outline-none transition hover:text-gray-900 focus-visible:ring-2 focus-visible:ring-gray-300 dark:text-gray-400 dark:hover:text-white"
			aria-expanded={open}
			on:click={() => (open = !open)}
		>
			<svg
				class="size-3 transition-transform duration-300 ease-out {open ? 'rotate-90' : ''}"
				viewBox="0 0 12 12"
				fill="none"
				stroke="currentColor"
				stroke-width="1.5"
				stroke-linecap="round"
				stroke-linejoin="round"
				aria-hidden="true"><path d="M4.5 2.5 8 6l-3.5 3.5" /></svg
			>
			What the server said
		</button>
	</div>

	<!-- Opens in place, height and all, so nothing below jumps. -->
	<div class="detail ml-10" class:open>
		<div>
			<p
				class="mt-1.5 select-text break-words rounded-xl bg-gray-50 px-3 py-2 font-mono text-[11.5px] leading-relaxed text-gray-600 dark:bg-gray-850 dark:text-gray-400"
			>
				{error?.detail}
			</p>
		</div>
	</div>
</div>

<style>
	.detail {
		display: grid;
		grid-template-rows: 0fr;
		opacity: 0;
		transition:
			grid-template-rows 320ms cubic-bezier(0.22, 1, 0.36, 1),
			opacity 240ms ease;
	}
	.detail > div {
		overflow: hidden;
	}
	/* A command and a server message are read character for character: no
	   ligature turns "--fix" into a dash. */
	.run-error :global(code),
	.detail p {
		font-variant-ligatures: none;
		font-feature-settings:
			'liga' 0,
			'calt' 0;
	}
	.detail.open {
		grid-template-rows: 1fr;
		opacity: 1;
	}
	@media (prefers-reduced-motion: reduce) {
		.detail,
		.run-error :global(svg) {
			transition: none !important;
		}
	}
</style>
