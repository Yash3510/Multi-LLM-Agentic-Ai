<script lang="ts">
	import Fuse from 'fuse.js';
	import Bolt from '$lib/components/icons/Bolt.svelte';
	import { getContext } from 'svelte';
	import { settings, WEBUI_NAME } from '$lib/stores';
	import { WEBUI_VERSION } from '$lib/constants';

	const i18n = getContext('i18n');

	export let suggestionPrompts = [];
	export let className = '';
	export let inputValue = '';
	export let onSelect = () => {};

	let sortedPrompts = [];

	/* An icon for the kind of work a suggestion starts, read from its words;
	   fixed markup, never taken from the prompt itself. */
	const ICONS = {
		code: '<path d="M5 5.5 2.5 8 5 10.5M11 5.5 13.5 8 11 10.5M9.25 3.5l-2.5 9" />',
		check: '<path d="M2.75 11a5.25 5.25 0 1 1 10.5 0" /><path d="M8 11l2.5-3.5" /><path d="M2.75 13.5h10.5" />',
		audit: '<path d="M8 1.75 13 3.75v3.9c0 3-2.1 5.4-5 6.6-2.9-1.2-5-3.6-5-6.6v-3.9z" /><path d="m5.75 8 1.6 1.6L10.5 6.5" />',
		document: '<path d="M4 1.75h5.25L12.5 5v9.25H4z" /><path d="M9 1.75V5h3.5M6 8.25h4M6 10.75h4" />',
		ask: '<path d="M2.75 3.75h10.5v7h-6L4 13.5v-2.75H2.75z" />'
	};
	const iconFor = (text: string) => {
		const t = (text ?? '').toLowerCase();
		if (/\b(code|python|script|run|sandbox|plot|chart|spreadsheet)\b/.test(t)) return 'code';
		if (/\b(threshold|limit|check|reading|sop|inspect|assess)/.test(t)) return 'check';
		if (/\b(audit|sovereign|secur|egress|comply|compliance)/.test(t)) return 'audit';
		if (/\b(report|document|summar|draft|note|write)/.test(t)) return 'document';
		return 'ask';
	};

	const fuseOptions = {
		keys: ['content', 'title'],
		threshold: 0.5
	};

	let fuse;
	let filteredPrompts = [];

	// Initialize Fuse
	$: fuse = new Fuse(sortedPrompts, fuseOptions);

	// Update the filteredPrompts if inputValue changes
	// Only increase version if something wirklich geändert hat
	$: getFilteredPrompts(inputValue);

	// Helper function to check if arrays are the same
	// (based on unique IDs oder content)
	function arraysEqual(a, b) {
		if (a.length !== b.length) return false;
		for (let i = 0; i < a.length; i++) {
			if ((a[i].id ?? a[i].content) !== (b[i].id ?? b[i].content)) {
				return false;
			}
		}
		return true;
	}

	const getFilteredPrompts = (inputValue) => {
		if (inputValue.length > 500) {
			filteredPrompts = [];
		} else {
			const newFilteredPrompts =
				inputValue.trim() && fuse
					? fuse.search(inputValue.trim()).map((result) => result.item)
					: sortedPrompts;

			// Compare with the oldFilteredPrompts
			// If there's a difference, update array + version
			if (!arraysEqual(filteredPrompts, newFilteredPrompts)) {
				filteredPrompts = newFilteredPrompts;
			}
		}
	};

	$: if (suggestionPrompts) {
		sortedPrompts = [...(suggestionPrompts ?? [])].sort(() => Math.random() - 0.5);
		getFilteredPrompts(inputValue);
	}
</script>

<div class="mb-1 flex gap-1 text-xs font-normal items-center text-gray-600 dark:text-gray-400">
	{#if filteredPrompts.length > 0}
		<Bolt />
		{$i18n.t('Suggested')}
	{:else}
		<!-- Keine Vorschläge -->

		<div
			class="flex w-full {$settings?.landingPageMode === 'chat'
				? ' -mt-1'
				: 'text-center items-center justify-center'}  self-start text-gray-600 dark:text-gray-400"
		>
			<!-- LICENSE covers this Open WebUI footer identifier.
			Do not alter, remove, obscure, or replace it except as LICENSE permits:
			https://docs.openwebui.com/license. -->
			{$WEBUI_NAME} ‧ v{WEBUI_VERSION}
		</div>
	{/if}
</div>

<div class="min-h-[4.5rem] w-full">
	{#if filteredPrompts.length > 0}
		<!-- Each suggestion a card: what it does and on what, with an icon for
		     the kind of work. They fall into a row when there is room. -->
		<div
			role="list"
			class="grid max-h-60 grid-cols-[repeat(auto-fit,minmax(11.5rem,1fr))] gap-2 overflow-auto scrollbar-none pb-1 {className}"
		>
			{#each filteredPrompts as prompt, idx (prompt.id || `${prompt.content}-${idx}`)}
				{@const title = prompt.title && prompt.title[0] !== '' ? prompt.title[0] : prompt.content}
				{@const detail = prompt.title && prompt.title[0] !== '' ? prompt.title[1] : $i18n.t('Prompt')}
				{@const icon = iconFor(`${title} ${detail} ${prompt.content}`)}
				<!-- svelte-ignore a11y-no-interactive-element-to-noninteractive-role -->
				<button
					role="listitem"
					class="waterfall group flex items-start gap-2.5 rounded-xl border border-gray-200/80 bg-white px-3 py-2.5 text-left transition-[border-color,box-shadow,transform] duration-200 hover:-translate-y-px hover:border-gray-300 hover:shadow-[0_8px_20px_-14px_rgba(16,24,40,0.3)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-900/15 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-gray-700"
					style="animation-delay: {idx * 45}ms"
					on:click={() => onSelect({ type: 'prompt', data: prompt.content })}
				>
					<span
						class="mt-px flex size-7 shrink-0 items-center justify-center rounded-lg border border-gray-100 bg-gray-50 text-gray-700 transition-colors group-hover:text-gray-900 dark:border-gray-800 dark:bg-gray-850 dark:text-gray-300 dark:group-hover:text-white"
						aria-hidden="true"
					>
						<svg
							class="size-3.5"
							viewBox="0 0 16 16"
							fill="none"
							stroke="currentColor"
							stroke-width="1.5"
							stroke-linecap="round"
							stroke-linejoin="round">{@html ICONS[icon]}</svg
						>
					</span>
					<span class="min-w-0 leading-snug">
						<span class="line-clamp-1 text-[13.5px] font-medium text-gray-900 dark:text-gray-100">{title}</span>
						<span class="line-clamp-1 text-[12px] text-gray-600 dark:text-gray-400">{detail}</span>
					</span>
				</button>
			{/each}
		</div>
	{/if}
</div>

<style>
	/* Waterfall animation for the suggestions */
	@keyframes fadeInUp {
		0% {
			opacity: 0;
			transform: translateY(6px);
		}
		100% {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.waterfall {
		opacity: 0;
		animation-name: fadeInUp;
		animation-duration: 200ms;
		animation-fill-mode: forwards;
		animation-timing-function: ease;
	}
</style>
