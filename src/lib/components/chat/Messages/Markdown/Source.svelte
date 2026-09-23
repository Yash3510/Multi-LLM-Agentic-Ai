<script lang="ts">
	import { getContext } from 'svelte';
	import { decodeString } from '$lib/utils';

	const i18n = getContext('i18n');

	export let id;

	export let title: string = 'N/A';

	/** Every source the answer can cite, to tell apart two that share a code. */
	export let siblings: string[] = [];

	export let onClick: Function = () => {};

	// Helper function to return only the domain from a URL
	function getDomain(url: string): string {
		const domain = url.replace('http://', '').replace('https://', '').split(/[/?#]/)[0];

		if (domain.startsWith('www.')) {
			return domain.slice(4);
		}
		return domain;
	}

	const getDisplayTitle = (title: string) => {
		if (!title) return 'N/A';
		if (title.length > 30) {
			return title.slice(0, 15) + '...' + title.slice(-10);
		}
		return title;
	};

	// Helper function to check if text is a URL and return the domain
	function formattedTitle(title: string): string {
		if (title.startsWith('http')) {
			return getDomain(title);
		}

		return title;
	}

	/* An evidence chip names the document, not the file: a document code such
	   as "SOP-MEC-014" when the name starts with one, otherwise the name
	   without its extension or underscores. When another source shares the
	   code (the SOP and a log of readings against it), the rest of the name
	   follows it, so the two chips never read the same. The full file name
	   is on hover and in the passage panel. */
	const bare = (title: string) => title.replace(/\.(pdf|docx?|md|txt|csv|xlsx?|pptx?|html?)$/i, '');
	const codeOf = (name: string) => name.match(/^[A-Z]{2,}(?:-[A-Z0-9]+)*-\d+/)?.[0] ?? null;
	const chipTitle = (title: string, others: string[]) => {
		if (title.startsWith('http')) return getDomain(title);
		const name = bare(title);
		const code = codeOf(name);
		if (!code) return name.replace(/_+/g, ' ');
		const shared = others
			.filter(Boolean)
			.map((other) => decodeString(other))
			.some((other) => other !== title && codeOf(bare(other)) === code);
		const rest = name.slice(code.length).replace(/^[\s_\-\u2013\u2014.]+/, '').replace(/_+/g, ' ').trim();
		return shared && rest ? `${code} · ${rest}` : code;
	};
</script>

{#if title !== 'N/A'}
	<!-- 4CE evidence chip: the document a claim rests on. Opens the exact
	     passage that was retrieved from it. -->
	<button
		aria-label={$i18n.t('View source: {{title}}', { title: formattedTitle(decodeString(title)) })}
		title={formattedTitle(decodeString(title))}
		class="evidence-chip inline-flex w-fit max-w-[16rem] translate-y-[1px] items-center gap-1 rounded-full border border-sky-200/80 bg-sky-50 px-1.5 py-px align-baseline text-[0.66rem] font-medium leading-[1.35] text-sky-800 transition hover:border-sky-300 hover:bg-sky-100 dark:border-sky-900/80 dark:bg-sky-950/50 dark:text-sky-200 dark:hover:border-sky-800 dark:hover:bg-sky-900/50"
		on:click={() => {
			onClick(id);
		}}
	>
		<svg
			class="size-[0.7rem] shrink-0 opacity-75"
			viewBox="0 0 16 16"
			fill="none"
			stroke="currentColor"
			stroke-width="1.6"
			stroke-linecap="round"
			stroke-linejoin="round"
			aria-hidden="true"
			><path d="M4 1.75h5.25L12.5 5v9.25H4z" /><path d="M9 1.75V5h3.5M6 8.25h4M6 10.75h4" /></svg
		>
		<span class="line-clamp-1">
			{getDisplayTitle(chipTitle(decodeString(title), siblings))}
		</span>
	</button>
{/if}
