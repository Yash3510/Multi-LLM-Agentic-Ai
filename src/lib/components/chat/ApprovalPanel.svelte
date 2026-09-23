<script context="module">
	import { writable } from 'svelte/store';

	/*
	 * Pending sign-offs, keyed by chat id. Module-level on purpose: navigating
	 * away and back rebuilds the chat page, and state held inside it was lost -
	 * measured: the backend was still "Awaiting human approval" with no panel
	 * left to answer it, so the run hung. The reply callback belongs to the
	 * socket connection, which survives in-app navigation, so the request can
	 * be kept here and answered later. A full page reload still drops it; the
	 * server-side timeout (WEBSOCKET_EVENT_CALLER_TIMEOUT) then withholds.
	 */
	export const pendingApprovals = writable({});
</script>

<script>
	/*
	 * ApprovalPanel - 4CE's sign-off, docked where the message box normally is.
	 *
	 * The approval used to be a modal: it darkened the conversation, so the
	 * reviewer could not compare the draft with the question or the sources
	 * while deciding. Here the conversation stays visible and scrollable above,
	 * and the draft sits in its own scrolling region below it.
	 *
	 * It is a review, not just a gate. Beside the draft sit the checks made
	 * before release (4CE's own figure check, then ULTRON's) and the sources;
	 * each [n] in the draft opens the passage it rests on; hovering a check
	 * lights the lines it speaks about; on a second try, the lines rewritten
	 * since the first can be shown beside what they replaced.
	 *
	 * The draft deliberately lives in this panel, not in the conversation:
	 * nothing enters the chat record until it is released. Withholding, closing
	 * the panel, or a timeout all leave the record without it.
	 *
	 * Releasing takes a hold of the button (or of Enter), about a second: a
	 * tap or a stray Enter does nothing, so nothing goes through by reflex -
	 * the reason the old dialog made you type a word. The panel only reports
	 * the decision: a completed hold sends "approve", withholding sends false,
	 * the values the old dialog sent, and the orchestrator withholds anything
	 * else regardless of what this component does.
	 */
	import { createEventDispatcher, onDestroy, onMount, tick } from 'svelte';
	import { fly } from 'svelte/transition';
	import { marked } from 'marked';
	import DOMPurify from 'dompurify';
	import { settings } from '$lib/stores';
	import { chipTitle } from './Messages/Markdown/evidence';
	import { chipCitations, matchChecks, findChanges } from './approvalReview';

	export let request = null;

	const dispatch = createEventDispatcher();

	$: data = request?.data ?? {};
	$: pass = data.verdict === 'PASS';
	$: checks = data.checks ?? [];
	$: sources = data.sources ?? [];
	$: revision = data.revision?.changes?.length ? data.revision : null;
	$: names = sources.map((s) => s.name);
	$: draftHtml = DOMPurify.sanitize(marked.parse(data.draft || '*The draft is empty.*'));
	$: verdictLabel = pass
		? (data.tries ?? 1) > 1
			? `Passed by ULTRON on try ${data.tries}`
			: 'Passed by ULTRON'
		: data.verdict === 'FAIL'
			? 'Did not pass its checks'
			: data.verdict === 'SKIPPED'
				? 'Not checked'
				: 'No verdict';

	/* ---- The draft and its reading aids ---- */
	let draftEl;
	let scroller;
	let checkBlocks = [];
	let changes = { placed: [], unplaced: [] };
	let showChanges = false;
	let openChip = null;

	function passageEl(source) {
		const box = document.createElement('div');
		box.className = 'rv-passage';
		const head = document.createElement('div');
		head.className = 'rv-passage-head';
		head.append(Object.assign(document.createElement('span'), { textContent: 'Passage' }));
		head.append(
			Object.assign(document.createElement('span'), {
				className: 'rv-passage-doc',
				textContent: chipTitle(source.name, names)
			})
		);
		if (source.match != null) {
			head.append(
				Object.assign(document.createElement('span'), {
					className: 'rv-passage-match',
					textContent: `${source.match}% match`
				})
			);
		}
		box.append(head, Object.assign(document.createElement('p'), { textContent: source.passage || 'No passage.' }));
		return box;
	}

	/* A chip opens its passage under the line it sits in; one open at a time. */
	function toggleChip(chip, source) {
		draftEl?.querySelectorAll('.rv-passage').forEach((n) => n.remove());
		draftEl?.querySelectorAll('.rv-cite.rv-on').forEach((n) => n.classList.remove('rv-on'));
		if (openChip === chip) {
			openChip = null;
			return;
		}
		openChip = chip;
		chip.classList.add('rv-on');
		const box = passageEl(source);
		const block = chip.closest('p, li, td, th, h1, h2, h3, h4, h5, h6') ?? chip;
		block.after(box);
		box.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
	}

	async function decorate() {
		await tick();
		if (!draftEl) return;
		openChip = null;
		chipCitations(draftEl, sources, toggleChip);
		checkBlocks = matchChecks(draftEl, checks);
		changes = findChanges(draftEl, revision);
		applyChanges(showChanges);
	}
	$: draftHtml, sources, checks, revision, decorate();

	/* Second try: the rewritten lines, each beside the line it replaced. */
	function applyChanges(on) {
		if (!draftEl) return;
		draftEl.querySelectorAll('.rv-old').forEach((n) => n.remove());
		draftEl.querySelectorAll('.rv-changed').forEach((n) => n.classList.remove('rv-changed'));
		if (!on) return;
		for (const { el, removed } of changes.placed) {
			el.classList.add('rv-changed');
			if (removed) {
				const old = document.createElement('span');
				old.className = 'rv-old';
				old.textContent = removed;
				el.prepend(old, ' ');
			}
		}
		changes.placed[0]?.el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
	}
	$: applyChanges(showChanges);

	/* Hovering a check lights the lines it speaks about. */
	function light(i, on) {
		for (const el of checkBlocks[i] ?? []) el.classList.toggle('rv-lit', on);
		if (on) checkBlocks[i]?.[0]?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
	}

	/* A source in the list: a cited one opens its first chip in the draft;
	   one only retrieved opens its passage in place. */
	let openSource = null;
	function openFromList(source) {
		const chip = draftEl?.querySelector(`.rv-cite[data-n="${source.n}"]`);
		if (chip) {
			if (openChip !== chip) toggleChip(chip, source);
			openSource = null;
		} else {
			openSource = openSource === source.n ? null : source.n;
		}
	}

	/* ---- Hold to release ---- */
	const HOLD = 900;
	let holdEl;
	let progress = 0;
	let holding = false;
	let released = false;
	let startedAt = 0;
	let frame = 0;
	let hint = '';

	function step() {
		progress = Math.min(1, (performance.now() - startedAt) / HOLD);
		if (progress >= 1) {
			finish();
			return;
		}
		frame = requestAnimationFrame(step);
	}
	function begin() {
		if (released || holding) return;
		holding = true;
		hint = '';
		startedAt = performance.now();
		cancelAnimationFrame(frame);
		frame = requestAnimationFrame(step);
	}
	function end() {
		if (released || !holding) return;
		holding = false;
		cancelAnimationFrame(frame);
		if (progress > 0.04) hint = 'Keep holding to release.';
		progress = 0;
	}
	function finish() {
		holding = false;
		released = true;
		progress = 1;
		// A beat to read "Released" before the panel gives way.
		setTimeout(() => dispatch('release', 'approve'), 320);
	}

	const withhold = () => {
		if (!released) dispatch('withhold');
	};

	/* Enter held anywhere but a field or another button releases; Esc
	   withholds. */
	const busyTarget = (t) =>
		t instanceof HTMLElement &&
		(t.isContentEditable || t.closest('input, textarea, select') || (t.closest('button') && t.closest('button') !== holdEl));
	function onKeydown(e) {
		if (e.key === 'Escape') {
			e.preventDefault();
			withhold();
		} else if (e.key === 'Enter' && !e.repeat && !e.isComposing && !busyTarget(e.target)) {
			e.preventDefault();
			begin();
		}
	}
	function onKeyup(e) {
		if (e.key === 'Enter') end();
	}

	onMount(async () => {
		await tick();
		holdEl?.focus({ preventScroll: true });
	});
	onDestroy(() => cancelAnimationFrame(frame));

	const CHECK_BY = (c) =>
		c.by === '4CE'
			? '4CE · no model'
			: c.kind === 'unverified'
				? 'ULTRON · could not check'
				: c.kind === 'problem'
					? 'ULTRON · a problem'
					: 'ULTRON';
</script>

<svelte:window on:keydown={onKeydown} on:keyup={onKeyup} />

<!-- px-2, not px-3: the same inset as the message box it replaces, so the two
     cards swap edge for edge (with px-3 it sat 4px inside on each side). -->
<div
	class="mx-auto w-full px-2 {($settings?.widescreenMode ?? null) ? 'max-w-full' : 'max-w-[58rem]'}"
	in:fly={{ y: 16, duration: 280 }}
>
	<div
		role="region"
		aria-label="Review before release"
		class="overflow-hidden rounded-[20px] border border-gray-100 bg-white ring-1 ring-black/[0.04] shadow-[0_1px_3px_-1px_rgba(16,24,40,0.08),0_20px_48px_-18px_rgba(16,24,40,0.28)] dark:border-gray-850 dark:bg-gray-900 dark:ring-white/[0.06]"
	>
		<!-- One text edge for the whole panel: 29px + the 1px border puts the
		     title, the objection and the hint on the same line as the text inside
		     the draft (12px inset + 1px border + 16px padding). -->
		<div class="flex flex-wrap items-center justify-between gap-x-4 gap-y-1.5 px-[29px] pb-3 pt-4">
			<div class="flex items-center gap-2.5">
				<span class="text-[0.9375rem] font-medium text-gray-900 dark:text-gray-100">
					Review before release
				</span>
				<span
					class="rounded-full px-2.5 py-0.5 text-[11px] font-medium {pass
						? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300'
						: 'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300'}"
				>
					{verdictLabel}
				</span>
			</div>
			<span class="text-xs text-gray-600 dark:text-gray-400">
				<span class="capitalize">{data.task_type ?? 'task'}</span> task · drafted on
				<code class="rounded bg-gray-100 px-1 py-0.5 text-[11px] dark:bg-gray-850">{data.model_id ?? ''}</code>
			</span>
		</div>

		{#if !pass && data.verdict_detail}
			<div class="px-[29px] pb-3 text-xs text-amber-700 dark:text-amber-300">
				<!-- A full sentence from the orchestrator (`_objection()`), naming who
				     objected - ULTRON, or 4CE's own figure check. -->
				{data.verdict_detail}
			</div>
		{/if}

		<div
			class="mx-3 mb-3 grid overflow-hidden rounded-2xl border border-gray-100 dark:border-gray-850 {checks.length ||
			sources.length
				? 'md:grid-cols-[minmax(0,1fr)_15rem]'
				: ''}"
		>
			<div
				bind:this={scroller}
				class="max-h-[42vh] overflow-y-auto bg-gray-50 px-4 py-4 dark:bg-gray-850/60"
			>
				{#if revision}
					<button
						type="button"
						class="mb-3 inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs transition {showChanges
							? 'border-gray-900 text-gray-900 dark:border-white dark:text-white'
							: 'border-gray-200 text-gray-600 hover:border-gray-400 hover:text-gray-900 dark:border-gray-700 dark:text-gray-300 dark:hover:border-gray-500 dark:hover:text-white'}"
						aria-pressed={showChanges}
						on:click={() => (showChanges = !showChanges)}
					>
						{showChanges ? 'Hide the changes' : 'Show what changed since try 1'}
					</button>
					{#if showChanges}
						<div
							class="mb-3 space-y-1 rounded-xl bg-amber-50 px-3 py-2 text-[12.5px] leading-relaxed text-amber-800 dark:bg-amber-950/40 dark:text-amber-200"
							in:fly={{ y: -4, duration: 260 }}
						>
							{#each revision.objections ?? [] as o}
								<p>{o.by ?? 'ULTRON'} on try 1: “{o.text}”</p>
							{/each}
							{#each changes.unplaced.filter((c) => c.removed && !c.added) as c}
								<p class="text-gray-600 dark:text-gray-400">
									Taken out: <span class="line-through">{c.removed.replace(/\s*\[\d+(?:\s*,\s*\d+)*\]/g, '')}</span>
								</p>
							{/each}
						</div>
					{/if}
				{/if}
				<div bind:this={draftEl} class="rv-draft markdown-prose text-gray-900 dark:text-gray-100">
					{@html draftHtml}
				</div>
			</div>

			{#if checks.length || sources.length}
				<div
					class="max-h-[42vh] overflow-y-auto border-t border-gray-100 bg-white px-3.5 py-3 text-[12.5px] dark:border-gray-850 dark:bg-gray-900 md:border-l md:border-t-0"
				>
					{#if checks.length}
						<div class="mb-1.5 text-[10.5px] font-medium uppercase tracking-[0.08em] text-gray-500 dark:text-gray-400">
							Checked
						</div>
						<ul class="mb-3 space-y-0.5">
							{#each checks as c, i}
								<li
									class="-mx-1.5 grid grid-cols-[0.9rem_minmax(0,1fr)] gap-1.5 rounded-lg px-1.5 py-1 text-gray-700 transition-colors hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-850"
									on:mouseenter={() => light(i, true)}
									on:mouseleave={() => light(i, false)}
								>
									<span
										class="pt-px text-[12px] font-semibold leading-[1.45] {c.kind === 'ok'
											? 'text-emerald-600 dark:text-emerald-400'
											: 'text-amber-600 dark:text-amber-400'}"
										aria-hidden="true">{c.kind === 'ok' ? '✓' : c.kind === 'problem' ? '!' : '?'}</span
									>
									<span class="leading-[1.45]">
										<span class="sr-only"
											>{c.kind === 'ok' ? 'Holds:' : c.kind === 'problem' ? 'Problem:' : 'Could not check:'}</span
										>{c.text}
										<span class="block text-[10.5px] tracking-[0.04em] text-gray-500 dark:text-gray-400">{CHECK_BY(c)}</span>
									</span>
								</li>
							{/each}
						</ul>
					{/if}
					{#if sources.length}
						<div class="mb-1.5 text-[10.5px] font-medium uppercase tracking-[0.08em] text-gray-500 dark:text-gray-400">
							Sources
						</div>
						<ul class="space-y-0.5">
							{#each sources as s}
								<li>
									<button
										type="button"
										class="-mx-1.5 flex w-[calc(100%+0.75rem)] items-baseline gap-2 rounded-lg px-1.5 py-1 text-left transition-colors hover:bg-gray-50 dark:hover:bg-gray-850"
										title={s.name}
										on:click={() => openFromList(s)}
									>
										<span
											class="min-w-0 truncate {s.cited
												? 'font-medium text-gray-900 dark:text-gray-100'
												: 'text-gray-600 dark:text-gray-400'}">{chipTitle(s.name, names)}</span
										>
										<span class="shrink-0 text-[10.5px] text-gray-500 dark:text-gray-400"
											>{s.cited ? 'cited' : 'not cited'}</span
										>
									</button>
									{#if openSource === s.n}
										<p
											class="mb-1 mt-0.5 rounded-xl bg-gray-50 px-2.5 py-2 text-[12px] leading-relaxed text-gray-600 dark:bg-gray-850 dark:text-gray-300"
											in:fly={{ y: -4, duration: 260 }}
										>
											{s.passage || 'No passage.'}
										</p>
									{/if}
								</li>
							{/each}
						</ul>
					{/if}
				</div>
			{/if}
		</div>

		<div class="flex flex-wrap items-center gap-2 px-3 pb-3">
			<p id="approval-hint" class="min-w-[12rem] flex-1 px-[17px] text-[11.5px] text-gray-600 dark:text-gray-400">
				{#if hint}
					<span class="text-gray-900 dark:text-gray-100">{hint}</span>
				{:else}
					Hold to release, or hold Enter. Esc withholds. Nothing enters the conversation until you
					release it.
				{/if}
			</p>
			<button
				type="button"
				on:click={withhold}
				class="flex-1 sm:flex-none shrink-0 rounded-full border border-gray-200 px-4 py-2.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-850"
			>
				Withhold
			</button>
			<!-- Hold, not click: the fill runs while it is held and drains back if
			     it is let go early. -->
			<button
				bind:this={holdEl}
				type="button"
				aria-describedby="approval-hint"
				class="hold relative flex-1 sm:flex-none shrink-0 select-none overflow-hidden rounded-full bg-gray-900 px-5 py-2.5 text-sm font-medium text-white outline-none transition-colors hover:bg-gray-800 focus-visible:ring-2 focus-visible:ring-gray-400 focus-visible:ring-offset-2 dark:bg-white dark:text-gray-900 dark:hover:bg-gray-100 dark:focus-visible:ring-offset-gray-900"
				style="touch-action: none;"
				on:pointerdown={(e) => {
					holdEl.setPointerCapture?.(e.pointerId);
					begin();
				}}
				on:pointerup={end}
				on:pointercancel={end}
				on:lostpointercapture={end}
				on:contextmenu|preventDefault
			>
				<span
					class="hold-fill pointer-events-none absolute inset-0 origin-left bg-white/25 dark:bg-gray-900/15"
					class:draining={!holding && !released}
					style="transform: scaleX({progress});"
					aria-hidden="true"
				></span>
				<span class="relative">{released ? 'Released' : holding ? 'Keep holding…' : 'Hold to release'}</span>
			</button>
		</div>
	</div>
</div>

<style>
	.hold-fill.draining {
		transition: transform 280ms ease;
	}

	/* The draft's chips, passages and marks, drawn into the rendered draft. */
	.rv-draft :global(.rv-cite.rv-on) {
		border-color: var(--color-gray-500, #9b9b9b);
		color: var(--color-gray-900, #1c1c1c);
	}
	:global(.dark) .rv-draft :global(.rv-cite.rv-on) {
		color: #fff;
	}
	.rv-draft :global(.rv-passage) {
		margin: 0.35rem 0 0.75rem;
		border: 1px solid var(--color-gray-100, #efefef);
		border-radius: 12px;
		background: #fff;
		padding: 0.6rem 0.75rem;
		box-shadow: 0 14px 30px -20px rgba(16, 24, 40, 0.35);
		animation: rv-rise 320ms cubic-bezier(0.22, 1, 0.36, 1);
	}
	:global(.dark) .rv-draft :global(.rv-passage) {
		border-color: var(--color-gray-800, #333);
		background: var(--color-gray-900, #1c1c1c);
	}
	.rv-draft :global(.rv-passage-head) {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.25rem;
		font-size: 11px;
		color: var(--color-gray-500, #9b9b9b);
	}
	.rv-draft :global(.rv-passage-doc) {
		color: var(--color-gray-700, #525252);
		font-weight: 500;
	}
	:global(.dark) .rv-draft :global(.rv-passage-doc) {
		color: var(--color-gray-300, #cdcdcd);
	}
	.rv-draft :global(.rv-passage-match) {
		border-radius: 9999px;
		background: #ecfdf5;
		color: #047857;
		padding: 0 0.45rem;
	}
	:global(.dark) .rv-draft :global(.rv-passage-match) {
		background: rgb(16 185 129 / 0.12);
		color: #6ee7b7;
	}
	.rv-draft :global(.rv-passage p) {
		margin: 0;
		font-size: 12.5px;
		line-height: 1.6;
		color: var(--color-gray-600, #676767);
	}
	:global(.dark) .rv-draft :global(.rv-passage p) {
		color: var(--color-gray-300, #cdcdcd);
	}
	/* A line a check speaks about, while the check is hovered. */
	.rv-draft :global(.rv-lit) {
		border-radius: 6px;
		background: rgb(139 92 246 / 0.09);
		box-shadow: 0 0 0 3px rgb(139 92 246 / 0.09);
		transition:
			background 300ms ease,
			box-shadow 300ms ease;
	}
	/* Second try: a rewritten line, with the line it replaced struck before it. */
	.rv-draft :global(.rv-changed) {
		border-radius: 6px;
		background: rgb(16 185 129 / 0.08);
		box-shadow: 0 0 0 3px rgb(16 185 129 / 0.08);
	}
	.rv-draft :global(.rv-old) {
		border-radius: 5px;
		background: rgb(239 68 68 / 0.08);
		padding: 0 0.25rem;
		color: #b91c1c;
		text-decoration: line-through;
		text-decoration-color: rgb(185 28 28 / 0.4);
	}
	:global(.dark) .rv-draft :global(.rv-old) {
		color: #fca5a5;
	}
	@keyframes rv-rise {
		from {
			opacity: 0;
			transform: translateY(-4px);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.rv-draft :global(.rv-passage) {
			animation: none;
		}
	}
</style>
