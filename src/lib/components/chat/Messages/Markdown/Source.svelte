<script lang="ts">
	import { getContext } from 'svelte';
	import { decodeString } from '$lib/utils';
	import { chipTitle, CHIP } from './evidence';

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

	// The chip names the document (see evidence.ts).
</script>

{#if title !== 'N/A'}
	<!-- 4CE evidence chip: the document a claim rests on. Opens the exact
	     passage that was retrieved from it. -->
	<button
		aria-label={$i18n.t('View source: {{title}}', { title: formattedTitle(decodeString(title)) })}
		title={formattedTitle(decodeString(title))}
		class={CHIP}
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
			{getDisplayTitle(
				decodeString(title).startsWith('http')
					? getDomain(decodeString(title))
					: chipTitle(decodeString(title), siblings.map((other) => decodeString(other ?? '')))
			)}
		</span>
	</button>
{/if}
