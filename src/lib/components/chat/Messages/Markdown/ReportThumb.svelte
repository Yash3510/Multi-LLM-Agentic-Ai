<script lang="ts">
	/*
	 * The first page of a Word report, drawn from the file itself (the same
	 * docx-preview renderer as the full preview) and scaled to fit `width`.
	 * Used for the hover preview on the report card.
	 */
	import { onDestroy, tick } from 'svelte';
	import { fade } from 'svelte/transition';
	import { fixDocxBullets } from '$lib/utils/docxBullets';
	import { docxReveal } from '$lib/utils/docxReveal';

	export let data: ArrayBuffer | null = null;
	export let width = 300;
	/** Read off the drawn report for a readable summary beside the page. */
	export let summary: {
		kind: string;
		opening: string;
		sections: string[];
		approvedBy: string;
		issued: string;
		pages: number;
	} | null = null;

	const text = (el: Element | null | undefined) => (el?.textContent ?? '').replace(/\s+/g, ' ').trim();
	// Running text without its raised citation numbers ("per minute¹" reads
	// "per minute1" as plain text).
	const prose = (el: Element | null | undefined) => {
		if (!el) return '';
		const copy = el.cloneNode(true) as Element;
		copy.querySelectorAll('sup, [style*="super"]').forEach((n) => n.remove());
		return text(copy);
	};
	/* The report's own layout (4ce/tools/deliverables.py): a masthead table,
	   the document type, the title, a table of details in label and value
	   pairs, then the body with its headings. */
	const summarise = (root: HTMLElement) => {
		const sheets = root.querySelectorAll('section.docx');
		const blocks = [...(sheets[0]?.querySelector('article')?.children ?? [])];
		const paras = blocks.filter((b) => b.tagName === 'P' && text(b));
		const details: Record<string, string> = {};
		const table = blocks.filter((b) => b.tagName === 'TABLE')[1];
		for (const cell of table?.querySelectorAll('td') ?? []) {
			const [label, value] = [...cell.querySelectorAll('p')].map(text);
			if (label && value) details[label.toLowerCase()] = value;
		}
		const afterTable = table ? blocks.slice(blocks.indexOf(table) + 1) : blocks;
		const opening = afterTable.find(
			(b) => b.tagName === 'P' && !/heading/i.test(b.className) && text(b).length > 40
		);
		return {
			kind: text(paras[0]).length < 40 ? text(paras[0]) : '',
			opening: prose(opening),
			sections: [...root.querySelectorAll('section.docx p[class*="heading"]')].map(text).filter(Boolean),
			approvedBy: details['approved by'] ?? '',
			issued: details['issued'] ?? '',
			pages: sheets.length
		};
	};

	let pages: HTMLDivElement;
	let styles: HTMLDivElement;
	let scale = 0.38;
	let ready = false;
	let failed = false;
	let run = 0;
	// The file this component has drawn, or is drawing: each is drawn once.
	// Without the guard the page was wiped and redrawn in a loop.
	let drawnFor: ArrayBuffer | null = null;

	const draw = async (buffer: ArrayBuffer | null) => {
		if (!buffer || !pages || buffer === drawnFor) return;
		drawnFor = buffer;
		const mine = ++run;
		ready = false;
		failed = false;
		try {
			const { renderAsync } = await import('docx-preview');
			if (mine !== run) return;
			pages.innerHTML = '';
			styles.innerHTML = '';
			await renderAsync(buffer.slice(0), pages, styles, {
				className: 'docx',
				inWrapper: false,
				breakPages: true,
				ignoreLastRenderedPageBreak: false,
				renderHeaders: true,
				renderFooters: true,
				useBase64URL: true
			});
			fixDocxBullets(styles);
			await tick();
			const first = pages.querySelector('section.docx') as HTMLElement | null;
			const pageWidth = first ? parseFloat(getComputedStyle(first).width) : 794;
			scale = width / (Number.isFinite(pageWidth) && pageWidth > 0 ? pageWidth : 794);
			summary = summarise(pages);
			ready = mine === run;
		} catch (error) {
			console.error('Report thumbnail:', error);
			failed = true;
		}
	};

	$: if (pages) draw(data);

	onDestroy(() => {
		run += 1;
	});
</script>

<div class="report-thumb relative overflow-hidden bg-white text-left" style="width: {width}px; height: {Math.round(width * 1.294)}px;">
	<div bind:this={styles}></div>
	<!-- Hidden until drawn; then the sheet rises and its lines settle in
	     (docxReveal, app.css). -->
	<div
		bind:this={pages}
		use:docxReveal
		class="origin-top-left"
		class:invisible={!ready}
		style="zoom: {scale};"
	></div>
	{#if !ready}
		<!-- Lines where the page will be, while it is drawn; they fade as it
		     comes up. -->
		<div
			class="absolute inset-0 {width < 160 ? 'space-y-1 p-2' : 'space-y-2 p-5'}"
			aria-hidden="true"
			out:fade={{ duration: 260 }}
		>
			{#if failed}
				<p class="pt-6 text-center text-[10px] text-gray-500">No preview</p>
			{:else}
				<div class="report-shimmer {width < 160 ? 'h-1' : 'h-2.5'} w-1/3 rounded bg-gray-100"></div>
				<div class="report-shimmer {width < 160 ? 'h-1.5' : 'h-4'} w-3/4 rounded bg-gray-100"></div>
				<div class="report-shimmer {width < 160 ? 'mt-1 h-3' : 'mt-4 h-10'} w-full rounded bg-gray-50"></div>
				{#each [1, 0.9, 0.95, 0.7, 1, 0.85] as w}
					<div class="report-shimmer {width < 160 ? 'h-1' : 'h-2'} rounded bg-gray-100" style="width: {w * 100}%"></div>
				{/each}
			{/if}
		</div>
	{/if}
</div>

<style>
	/* Only the first page, with no gap or shadow round it. */
	.report-thumb :global(section.docx) {
		margin: 0 !important;
		box-shadow: none !important;
	}
	.report-thumb :global(section.docx ~ section.docx) {
		display: none !important;
	}
	.report-shimmer {
		animation: report-shimmer 1.2s ease-in-out infinite;
	}
	@keyframes report-shimmer {
		50% {
			opacity: 0.5;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.report-shimmer {
			animation: none;
		}
	}
</style>
