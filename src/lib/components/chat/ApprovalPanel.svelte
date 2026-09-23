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
	 * The draft deliberately lives in this panel, not in the conversation:
	 * nothing enters the chat record until it is released. Withholding, closing
	 * the panel, or a timeout all leave the record without it.
	 *
	 * The panel only reports the decision. The orchestrator still makes it:
	 * `release` sends the typed text and `withhold` sends false - the same
	 * values the old dialog sent - and anything other than "approve" is
	 * withheld server-side regardless of what this component does.
	 */
	import { createEventDispatcher, onMount, tick } from 'svelte';
	import { fly } from 'svelte/transition';
	import { marked } from 'marked';
	import DOMPurify from 'dompurify';
	import { settings } from '$lib/stores';

	export let request = null;

	const dispatch = createEventDispatcher();

	let value = '';
	let hint = '';
	let inputEl;

	$: data = request?.data ?? {};
	$: pass = data.verdict === 'PASS';
	$: ready = /^\s*approved?\s*$/i.test(value);
	$: draftHtml = DOMPurify.sanitize(marked.parse(data.draft || '*The draft is empty.*'));
	$: if (value) hint = '';

	const release = () => {
		if (!ready) {
			// Say what is missing rather than sending a decision that will only
			// come back as "withheld" - the confusion the old placeholder caused.
			hint = 'Type approve to release it.';
			inputEl?.focus();
			return;
		}
		dispatch('release', value.trim());
	};

	const withhold = () => dispatch('withhold');

	const onKey = (e) => {
		if (e.key === 'Enter') {
			e.preventDefault();
			release();
		} else if (e.key === 'Escape') {
			e.preventDefault();
			withhold();
		}
	};

	onMount(async () => {
		await tick();
		inputEl?.focus();
	});
</script>

<!-- px-2, not px-3: the same inset as the message box it replaces, so the two
     cards swap edge for edge (with px-3 it sat 4px inside on each side). -->
<div
	class="mx-auto w-full px-2 {($settings?.widescreenMode ?? null) ? 'max-w-full' : 'max-w-[58rem]'}"
	in:fly={{ y: 16, duration: 280 }}
>
	<div
		role="region"
		aria-label="Review before release"
		class="overflow-hidden rounded-2xl border border-gray-100 bg-white ring-1 ring-black/[0.04] shadow-[0_1px_3px_-1px_rgba(16,24,40,0.08),0_20px_48px_-18px_rgba(16,24,40,0.28)] dark:border-gray-850 dark:bg-gray-900 dark:ring-white/[0.06]"
	>
		<!-- One text edge for the whole panel: 29px + the 1px border puts the
		     title, the objection and the hint on the same line as the text inside
		     the draft and the input (12px inset + 1px border + 16px padding).
		     They were at 21, 34 and 30px. -->
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
					ULTRON: {data.verdict ?? 'UNKNOWN'}
				</span>
			</div>
			<span class="text-xs text-gray-500 dark:text-gray-400">
				{data.task_type ?? 'task'} · drafted on
				<code class="rounded bg-gray-100 px-1 py-0.5 text-[11px] dark:bg-gray-850">{data.model_id ?? ''}</code>
			</span>
		</div>

		{#if !pass && data.verdict_detail}
			<div class="px-[29px] pb-3 text-xs text-amber-700 dark:text-amber-300">
				ULTRON's objection: {data.verdict_detail}
			</div>
		{/if}

		<div
			class="markdown-prose mx-3 mb-3 max-h-[42vh] overflow-y-auto rounded-[10px] border border-gray-100 bg-gray-50 px-4 py-4 text-gray-900 dark:border-gray-850 dark:bg-gray-850/60 dark:text-gray-100"
		>
			{@html draftHtml}
		</div>

		<!-- On phones the input takes its own row: squeezed beside two buttons it
		     truncated to "Type approve to r…". -->
		<div class="flex flex-wrap items-center gap-2 px-3 pb-2">
			<input
				bind:this={inputEl}
				bind:value
				on:keydown={onKey}
				type="text"
				autocomplete="off"
				spellcheck="false"
				placeholder="Type approve to release"
				aria-label="Type approve to release"
				aria-describedby="approval-hint"
				class="min-w-0 w-full sm:w-auto sm:flex-1 rounded-[10px] border border-gray-100 bg-gray-50 px-4 py-2.5 text-sm text-gray-900 outline-none transition focus:border-gray-300 dark:border-gray-800 dark:bg-gray-850 dark:text-gray-100 dark:focus:border-gray-600"
			/>
			<button
				type="button"
				on:click={withhold}
				class="flex-1 sm:flex-none shrink-0 rounded-full border border-gray-200 px-4 py-2.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-850"
			>
				Withhold
			</button>
			<button
				type="button"
				on:click={release}
				class="flex-1 sm:flex-none shrink-0 rounded-full px-5 py-2.5 text-sm font-medium transition {ready
					? 'bg-gray-900 text-white hover:bg-gray-800 dark:bg-white dark:text-gray-900 dark:hover:bg-gray-100'
					: 'bg-gray-100 text-gray-400 dark:bg-gray-850 dark:text-gray-500'}"
			>
				Release
			</button>
		</div>

		<div id="approval-hint" class="px-[29px] pb-3.5 text-[11.5px] text-gray-500 dark:text-gray-400">
			{#if hint}
				<span class="text-amber-700 dark:text-amber-300">{hint}</span>
			{:else}
				Nothing enters the conversation until you release it. Withhold, press Esc, or leave it -
				anything other than approve keeps it back.
			{/if}
		</div>
	</div>
</div>
