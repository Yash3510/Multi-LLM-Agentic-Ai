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
		<div class="absolute inset-0 space-y-2 p-5" aria-hidden="true" out:fade={{ duration: 260 }}>
			{#if failed}
				<p class="pt-10 text-center text-xs text-gray-500">The preview could not be drawn.</p>
			{:else}
				<div class="report-shimmer h-2.5 w-1/3 rounded bg-gray-100"></div>
				<div class="report-shimmer h-4 w-3/4 rounded bg-gray-100"></div>
				<div class="report-shimmer mt-4 h-10 w-full rounded bg-gray-50"></div>
				{#each [1, 0.9, 0.95, 0.7, 1, 0.85] as w}
					<div class="report-shimmer h-2 rounded bg-gray-100" style="width: {w * 100}%"></div>
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
