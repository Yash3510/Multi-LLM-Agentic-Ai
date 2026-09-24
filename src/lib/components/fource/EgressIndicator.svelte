<script lang="ts">
	/**
	 * 4CE: the egress count, in the navbar from the first click to the last.
	 *
	 * The briefing's point about D5 is that the proof should cover every other
	 * demonstration at once - so it sits on screen while they run, rather than
	 * on a page someone has to remember to open. Admins only: the Navbar
	 * decides, and the endpoint refuses anyone else.
	 */
	import { onDestroy, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { getEgress, type Egress } from '$lib/apis/fource';

	let egress: Egress | null = null;
	let timer: ReturnType<typeof setInterval>;

	const poll = async () => {
		try {
			egress = await getEgress(localStorage.token);
		} catch {
			egress = null;
		}
	};

	onMount(() => {
		poll();
		timer = setInterval(poll, 3000);
	});
	onDestroy(() => clearInterval(timer));

	const span = (seconds: number) =>
		seconds < 90
			? `${Math.round(seconds)} s`
			: seconds < 5400
				? `${Math.round(seconds / 60)} min`
				: `${Math.floor(seconds / 3600)} h ${Math.round((seconds % 3600) / 60)} min`;

	$: external = egress?.flows?.external ?? 0;
	$: lanOut = egress?.flows?.lan_out ?? 0;
	// Sampling, and recently: a watch that stopped is not evidence of anything.
	$: sampling = !!egress?.running && !egress?.error && egress.now - egress.last_sample < 5;
	$: state = !sampling ? 'stale' : external || lanOut ? 'alert' : 'clean';
	$: tip = !egress
		? ''
		: state === 'stale'
			? 'The egress watch is not sampling, so nothing is being observed.'
			: state === 'alert'
				? `${external} external and ${lanOut} other outbound LAN connections seen in the last ${span(egress.now - egress.since)}. Open the Sovereignty page.`
				: `No external connections from ${egress.scope.length} workbench processes in the last ${span(egress.now - egress.since)}, ${egress.samples.toLocaleString()} samples. Open the Sovereignty page.`;
</script>

{#if egress}
	<Tooltip content={tip}>
		<button
			class="egress flex h-6 items-center gap-1.5 rounded-full border px-2 text-xs transition {state ===
			'alert'
				? 'border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300'
				: state === 'stale'
					? 'border-dashed border-gray-300 text-gray-500 dark:border-gray-700 dark:text-gray-500'
					: 'border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-800 dark:text-gray-300 dark:hover:bg-gray-850'}"
			on:click={() => goto('/sovereignty')}
			aria-label="Egress: {state === 'stale'
				? 'not observed'
				: `${external} external connection${external === 1 ? '' : 's'}`}. Open the Sovereignty page."
		>
			<span
				class="dot size-1.5 rounded-full {state === 'alert'
					? 'bg-amber-500'
					: state === 'stale'
						? 'bg-gray-400'
						: 'bg-emerald-500'}"
				class:live={state === 'clean'}
			></span>
			{#if state === 'stale'}
				<span>egress not observed</span>
			{:else}
				<span class="tabular-nums font-medium">{external}</span>
				<span class="hidden sm:inline">external</span>
			{/if}
		</button>
	</Tooltip>
{/if}

<style>
	.live {
		animation: egress-breathe 2.4s ease-in-out infinite;
	}
	@keyframes egress-breathe {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.35;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.live {
			animation: none;
		}
	}
</style>
