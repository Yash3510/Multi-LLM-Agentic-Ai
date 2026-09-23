<script lang="ts">
	/*
	 * A document 4CE wrote for an answer - the Word report - as a card: what
	 * it is, its size, where it is kept, and a download button. The
	 * orchestrator writes it as a ```4ce-file block of JSON (`_file_card()` in
	 * 4ce/functions/orchestrator.py).
	 */
	import { WEBUI_BASE_URL } from '$lib/constants';

	export let data: { kind?: string; title?: string; kb?: number; url?: string; note?: string };

	$: href = data.url?.startsWith('/api/') ? `${WEBUI_BASE_URL}${data.url}` : (data.url ?? '');
	$: kind = data.kind ?? 'Word report';
</script>

<div
	class="file-card not-prose my-3 flex w-full max-w-xl items-center gap-3 rounded-xl border border-gray-200/90 bg-white py-2.5 pl-2.5 pr-3 transition-[border-color,box-shadow] duration-200 hover:border-gray-300 hover:shadow-[0_6px_18px_-12px_rgba(16,24,40,0.25)] dark:border-gray-800 dark:bg-gray-900 dark:hover:border-gray-700"
>
	<!-- The page, folded at the corner, in the chat's ink: the report is
	     4CE's own document, not a link out. -->
	<span
		class="flex size-10 shrink-0 items-center justify-center rounded-[10px] border border-gray-100 bg-gray-50 text-gray-800 dark:border-gray-800 dark:bg-gray-850 dark:text-gray-100"
		aria-hidden="true"
	>
		<svg
			class="size-5"
			viewBox="0 0 16 16"
			fill="none"
			stroke="currentColor"
			stroke-width="1.3"
			stroke-linecap="round"
			stroke-linejoin="round"
			><path d="M4 1.75h5.25L12.5 5v9.25H4z" /><path d="M9 1.75V5h3.5M6 8.25h4M6 10.75h4" /></svg
		>
	</span>

	<span class="min-w-0 flex-1">
		<span
			class="line-clamp-1 text-[13px] font-medium leading-5 text-gray-900 dark:text-gray-100"
			title={data.title || kind}>{data.title || kind}</span
		>
		<span class="line-clamp-1 text-[11.5px] leading-4 text-gray-600 dark:text-gray-400">
			{kind}{data.kb ? ` · ${data.kb} KB` : ''} · stored on this machine
		</span>
	</span>

	{#if href}
		<a
			{href}
			class="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-gray-200 px-3.5 py-1.5 text-xs font-medium text-gray-800 no-underline transition hover:bg-gray-50 hover:text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-900/15 dark:border-gray-700 dark:text-gray-100 dark:hover:bg-gray-850 dark:hover:text-white"
			download
			aria-label="Download {data.title || kind}"
		>
			<svg
				class="size-3.5"
				viewBox="0 0 16 16"
				fill="none"
				stroke="currentColor"
				stroke-width="1.6"
				stroke-linecap="round"
				stroke-linejoin="round"
				aria-hidden="true"><path d="M8 2.5v8M4.75 7.5 8 10.75 11.25 7.5M3 13.25h10" /></svg
			>
			Download
		</a>
	{/if}
</div>
{#if data.note}
	<p class="-mt-1.5 mb-3 text-xs text-gray-600 dark:text-gray-400">{data.note.replace(/`/g, '')}</p>
{/if}

<style>
	/* The card settles in when the report is written in front of the reader;
	   an answer opened later draws it still. */
	:global(.message-in) .file-card {
		animation: file-card-in 360ms cubic-bezier(0.2, 0.7, 0.2, 1) backwards;
	}
	@keyframes file-card-in {
		from {
			opacity: 0;
			transform: translateY(4px);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		:global(.message-in) .file-card {
			animation: none;
		}
	}
</style>
