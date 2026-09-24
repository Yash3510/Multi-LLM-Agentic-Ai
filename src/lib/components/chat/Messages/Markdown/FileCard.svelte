<script lang="ts">
	/*
	 * A document 4CE wrote for an answer - the Word report - as a card: what
	 * it is, its size, where it is kept. Hovering its page shows the first
	 * page of the real file; clicking the card opens the whole report to read;
	 * the file is saved only from the Download button. The orchestrator writes
	 * the card as a ```4ce-file block of JSON (`_file_card()` in
	 * 4ce/functions/orchestrator.py).
	 */
	import { onDestroy } from 'svelte';
	import { WEBUI_BASE_URL } from '$lib/constants';
	import { getFileContentById } from '$lib/apis/files';
	import Modal from '$lib/components/common/Modal.svelte';
	import DocxPreview from '$lib/components/common/DocxPreview.svelte';
	import ReportThumb from './ReportThumb.svelte';
	import { fade } from 'svelte/transition';
	import { expoOut } from 'svelte/easing';
	import { docxReveal } from '$lib/utils/docxReveal';

	/* The preview grows out of the page icon: a soft deceleration, a touch of
	   scale and a 2px blur that clears as it lands. */
	const lift = (_node: Element, { duration = 460 } = {}) => ({
		duration,
		easing: expoOut,
		css: (t: number, u: number) =>
			`opacity: ${Math.min(1, t * 1.6)}; transform: translateY(${-8 * u}px) scale(${0.94 + 0.06 * t}); filter: blur(${2 * u}px);`
	});

	export let data: { kind?: string; title?: string; kb?: number; url?: string; note?: string };

	$: href = data.url?.startsWith('/api/') ? `${WEBUI_BASE_URL}${data.url}` : (data.url ?? '');
	$: kind = data.kind ?? 'Word report';
	// A workbook or a deck downloads; only a Word report has a page to preview.
	$: format = /excel|workbook/i.test(kind) ? 'xlsx' : /powerpoint|deck/i.test(kind) ? 'pptx' : 'docx';
	$: previewable = format === 'docx';
	let downloadEl: HTMLAnchorElement;
	$: fileId = data.url?.match(/\/files\/([^/]+)\/content/)?.[1] ?? null;

	/* The file is fetched once, the first time it is looked at, and kept. */
	let file: ArrayBuffer | null = null;
	let summary = null;
	let loading: Promise<void> | null = null;
	let failed = false;
	const load = () =>
		(loading ??= (async () => {
			try {
				file = fileId ? await getFileContentById(fileId) : null;
				failed = !file;
			} catch {
				failed = true;
			}
		})());

	/* Hover: a short pause before the preview shows, so moving the pointer
	   across the chat does not flash it, and a grace period when leaving, so
	   the pointer can travel onto the preview. */
	let peek = false;
	let showTimer: ReturnType<typeof setTimeout>;
	let hideTimer: ReturnType<typeof setTimeout>;
	const enter = () => {
		if (!previewable) return;
		clearTimeout(hideTimer);
		load();
		showTimer = setTimeout(() => (peek = true), 280);
	};
	const leave = () => {
		clearTimeout(showTimer);
		hideTimer = setTimeout(() => (peek = false), 160);
	};

	let open = false;
	const read = () => {
		if (!previewable) {
			downloadEl?.click();
			return;
		}
		clearTimeout(showTimer);
		peek = false;
		load();
		open = true;
	};

	onDestroy(() => {
		clearTimeout(showTimer);
		clearTimeout(hideTimer);
	});

	const DOWNLOAD =
		'inline-flex shrink-0 items-center gap-1.5 rounded-full border border-gray-200 px-3.5 py-1.5 text-xs font-medium text-gray-800 no-underline transition hover:bg-gray-50 hover:text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-900/15 dark:border-gray-700 dark:text-gray-100 dark:hover:bg-gray-850 dark:hover:text-white';
</script>

<div class="file-card-wrap relative my-3 w-full max-w-xl">
	<div
		class="file-card not-prose flex w-full items-center gap-3 rounded-2xl border border-gray-200/90 bg-white py-2.5 pl-2.5 pr-3 transition-[border-color,box-shadow] duration-200 hover:border-gray-300 hover:shadow-[0_6px_18px_-12px_rgba(16,24,40,0.25)] dark:border-gray-800 dark:bg-gray-900 dark:hover:border-gray-700"
	>
		<!-- The page and the title open the report to read; hovering them shows
		     its first page. -->
		<button
			type="button"
			class="flex min-w-0 flex-1 items-center gap-3 rounded-lg text-left outline-none focus-visible:ring-2 focus-visible:ring-gray-900/15"
			aria-label="{previewable ? 'Preview' : 'Download'} {data.title || kind}"
			aria-haspopup={previewable ? 'dialog' : undefined}
			on:mouseenter={enter}
			on:mouseleave={leave}
			on:focus={enter}
			on:blur={leave}
			on:click={read}
		>
			<!-- The page, folded at the corner, in the chat's ink: the report is
			     4CE's own document, not a link out. -->
			<span
				class="flex size-10 shrink-0 items-center justify-center rounded-[10px] border bg-gray-50 text-gray-800 transition-[border-color,transform] duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] dark:bg-gray-850 dark:text-gray-100 {peek
					? '-translate-y-0.5 -rotate-3 border-gray-300 dark:border-gray-600'
					: 'border-gray-100 dark:border-gray-800'}"
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
					>{#if format === 'xlsx'}<path d="M2.75 2.75h10.5v10.5H2.75z" /><path
							d="M2.75 6.25h10.5M2.75 9.75h10.5M6.75 2.75v10.5"
						/>{:else if format === 'pptx'}<path d="M2 3h12v8H2z" /><path
							d="M8 11v2.5M5.5 13.5h5M4.5 5.75h4M4.5 8.25h6"
						/>{:else}<path d="M4 1.75h5.25L12.5 5v9.25H4z" /><path
							d="M9 1.75V5h3.5M6 8.25h4M6 10.75h4"
						/>{/if}</svg
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
		</button>

		{#if href}
			<a {href} class={DOWNLOAD} download aria-label="Download {data.title || kind}" bind:this={downloadEl}>
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

	{#if peek && fileId && previewable}
		<!-- svelte-ignore a11y-no-static-element-interactions -->
		<div
			class="report-peek absolute left-0 top-full z-30 mt-2 origin-[22px_-10px] overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-[0_24px_60px_-24px_rgba(16,24,40,0.45)] dark:border-gray-700 dark:bg-gray-900"
			in:lift
			out:fade={{ duration: 140 }}
			on:mouseenter={enter}
			on:mouseleave={leave}
		>
			{#if failed}
				<p class="w-[300px] px-4 py-6 text-center text-xs text-gray-600 dark:text-gray-400">
					The report could not be loaded for a preview. It can still be downloaded.
				</p>
			{:else}
				<!-- The page for its look, beside what it says in type you can read. -->
				<div class="flex w-[26rem] max-w-[calc(100vw-3rem)] gap-3.5 p-3.5">
					<button
						type="button"
						class="shrink-0 self-start overflow-hidden rounded-lg border border-gray-200 shadow-[0_6px_16px_-10px_rgba(16,24,40,0.35)] dark:border-gray-700"
						aria-label="Open the full report"
						on:click={read}
					>
						<ReportThumb data={file} width={104} bind:summary />
					</button>
					<div class="min-w-0 flex-1">
						<div class="peek-line text-[10.5px] font-medium uppercase tracking-[0.08em] text-gray-600 dark:text-gray-400" style="--i: 0">
							{summary?.kind || kind}
						</div>
						<div
							class="peek-line mt-0.5 line-clamp-2 text-[14px] font-semibold leading-snug text-gray-900 dark:text-white"
							style="--i: 1"
						>
							{data.title || kind}
						</div>
						{#if summary?.opening}
							<p class="peek-line mt-1.5 line-clamp-4 text-[12.5px] leading-[1.55] text-gray-700 dark:text-gray-300" style="--i: 2">
								{summary.opening}
							</p>
						{:else}
							<div class="mt-2 space-y-1.5" aria-hidden="true">
								{#each [1, 0.92, 0.7] as w}
									<div class="report-bar h-2 rounded bg-gray-100 dark:bg-gray-800" style="width: {w * 100}%"></div>
								{/each}
							</div>
						{/if}
					</div>
				</div>
				{#if summary?.sections?.length}
					<div class="flex flex-wrap gap-1.5 px-3.5 pb-3">
						{#each summary.sections.slice(0, 6) as section, k}
							<span
								class="peek-line rounded-full border border-gray-200 px-2 py-0.5 text-[11px] leading-4 text-gray-700 dark:border-gray-700 dark:text-gray-300"
								style="--i: {3 + k}">{section}</span
							>
						{/each}
					</div>
				{/if}
				<div
					class="report-peek-foot flex items-center justify-between gap-3 border-t border-gray-100 px-3.5 py-2 text-[11.5px] text-gray-600 dark:border-gray-800 dark:text-gray-400"
				>
					<span class="min-w-0 truncate"
						>{[
							summary?.approvedBy ? `Approved by ${summary.approvedBy}` : '',
							`${summary?.pages ?? 1} ${(summary?.pages ?? 1) === 1 ? 'page' : 'pages'}`
						]
							.filter(Boolean)
							.join(' · ')}</span
					>
					<span class="shrink-0 font-medium text-gray-900 dark:text-gray-100">Click to read</span>
				</div>
			{/if}
		</div>
	{/if}
</div>
{#if data.note}
	<p class="-mt-1.5 mb-3 text-xs text-gray-600 dark:text-gray-400">{data.note.replace(/`/g, '')}</p>
{/if}

<Modal size="lg" bind:show={open}>
	<div class="flex max-h-[88vh] flex-col">
		<div class="flex items-center gap-3 border-b border-gray-100 px-5 py-3 dark:border-gray-850">
			<div class="min-w-0 flex-1">
				<div class="line-clamp-1 text-sm font-semibold text-gray-900 dark:text-white">{data.title || kind}</div>
				<div class="text-[11.5px] text-gray-600 dark:text-gray-400">
					{kind}{data.kb ? ` · ${data.kb} KB` : ''} · stored on this machine
				</div>
			</div>
			{#if href}
				<a {href} class={DOWNLOAD} download>Download</a>
			{/if}
			<button
				type="button"
				class="rounded-lg p-1.5 text-gray-500 transition hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-white"
				aria-label="Close the preview"
				on:click={() => (open = false)}
			>
				<svg class="size-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8" /></svg>
			</button>
		</div>
		<div class="h-[75vh] bg-gray-50 dark:bg-gray-950" use:docxReveal>
			{#if failed}
				<p class="p-6 text-center text-sm text-gray-600 dark:text-gray-400">
					The report could not be loaded. It can still be downloaded.
				</p>
			{:else if open}
				<DocxPreview data={file} className="h-full" />
			{/if}
		</div>
	</div>
</Modal>

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
	/* The summary's lines settle in one after another, like the page's. */
	.peek-line {
		animation: peek-line-in 520ms calc(120ms + var(--i, 0) * 45ms) cubic-bezier(0.16, 1, 0.3, 1) both;
	}
	@keyframes peek-line-in {
		from {
			opacity: 0;
			transform: translateY(4px);
		}
	}
	.report-bar {
		animation: report-bar 1.2s ease-in-out infinite;
	}
	@keyframes report-bar {
		50% {
			opacity: 0.5;
		}
	}
	/* The preview's footer comes last, once the page is up. */
	.report-peek-foot {
		animation: report-foot-in 420ms 360ms cubic-bezier(0.16, 1, 0.3, 1) both;
	}
	@keyframes report-foot-in {
		from {
			opacity: 0;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		:global(.message-in) .file-card,
		.report-peek-foot,
		.peek-line,
		.report-bar {
			animation: none;
		}
	}
</style>
