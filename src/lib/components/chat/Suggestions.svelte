<script lang="ts">
	import Fuse from 'fuse.js';
	import { getContext } from 'svelte';
	import { settings, WEBUI_NAME } from '$lib/stores';
	import { WEBUI_VERSION } from '$lib/constants';

	const i18n = getContext('i18n');

	export let suggestionPrompts = [];
	export let className = '';
	export let inputValue = '';
	export let onSelect = () => {};

	let sortedPrompts = [];

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
		<!-- The list's name, in the rail's small capitals. -->
		<span class="px-2.5 text-[10.5px] font-medium uppercase tracking-[0.08em] text-gray-600 dark:text-gray-400"
			>{$i18n.t('Suggested')}</span
		>
	{:else}
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

<div class="w-full">
	{#if filteredPrompts.length > 0}
		<!-- Each suggestion on two lines: the task, then what it works on. A
		     hairline between them; on hover the row lifts to a soft fill and an
		     arrow slides in. -->
		<div role="list" class="max-h-60 overflow-auto scrollbar-none {className}">
			{#each filteredPrompts as prompt, idx (prompt.id || `${prompt.content}-${idx}`)}
				{@const hasTitle = prompt.title && prompt.title[0] !== ''}
				<!-- svelte-ignore a11y-no-interactive-element-to-noninteractive-role -->
				<button
					role="listitem"
					class="sug-row waterfall group relative flex w-full items-center gap-3 rounded-[10px] px-2.5 py-2 text-left transition-colors hover:bg-gray-50 focus-visible:bg-gray-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-200 dark:border-gray-850 dark:hover:bg-gray-850/60 dark:focus-visible:bg-gray-850/60 dark:focus-visible:ring-gray-800"
					style="animation-delay: {idx * 45}ms"
					on:click={() => onSelect({ type: 'prompt', data: prompt.content })}
				>
					<span class="flex min-w-0 flex-1 flex-col leading-snug">
						<span
							class="line-clamp-1 text-[13.5px] text-gray-800 transition-colors group-hover:text-gray-900 dark:text-gray-200 dark:group-hover:text-white"
							>{hasTitle ? prompt.title[0] : prompt.content}</span
						>
						<span
							class="line-clamp-1 text-[12px] text-gray-600 transition-colors group-hover:text-gray-700 dark:text-gray-400 dark:group-hover:text-gray-300"
							>{hasTitle ? prompt.title[1] : $i18n.t('Prompt')}</span
						>
					</span>
					<svg
						class="size-3.5 shrink-0 -translate-x-1 text-gray-400 opacity-0 transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:translate-x-0 group-hover:opacity-100 group-focus-visible:translate-x-0 group-focus-visible:opacity-100 dark:text-gray-500"
						viewBox="0 0 16 16"
						fill="none"
						stroke="currentColor"
						stroke-width="1.6"
						stroke-linecap="round"
						stroke-linejoin="round"
						aria-hidden="true"><path d="M3 8h9.5M9 4.5 12.5 8 9 11.5" /></svg
					>
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
		animation-duration: 320ms;
		animation-fill-mode: forwards;
		animation-timing-function: cubic-bezier(0.22, 1, 0.36, 1);
	}
	/* Hairlines between rows, inset so they stop short of the rounded
	   corners; the ones touching a hovered row step aside. */
	.sug-row::after {
		content: '';
		position: absolute;
		left: 10px;
		right: 10px;
		bottom: 0;
		height: 1px;
		background: var(--color-gray-100, #efefef);
		transition: opacity 200ms ease;
	}
	:global(.dark) .sug-row::after {
		background: var(--color-gray-850, #262626);
	}
	.sug-row:last-child::after,
	.sug-row:hover::after,
	.sug-row:has(+ .sug-row:hover)::after {
		opacity: 0;
	}

	@media (prefers-reduced-motion: reduce) {
		.waterfall {
			opacity: 1;
			animation: none;
		}
	}
</style>
