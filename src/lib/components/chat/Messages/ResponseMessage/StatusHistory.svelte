<script>
	import { getContext } from 'svelte';
	const i18n = getContext('i18n');

	import StatusItem from './StatusHistory/StatusItem.svelte';
	import LiveStatusLine, { FOURCE_ACTIONS } from './StatusHistory/LiveStatusLine.svelte';
	import { fly } from 'svelte/transition';
	import equal from 'fast-deep-equal';
	export let statusHistory = [];
	export let expand = false;
	/** The stage rail above (StageRail's `live`): where it is, so this line
	    keeps pace with it rather than with the raw status stream. */
	export let rail = null;

	const reduced =
		typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

	let showHistory = true;

	$: if (expand) {
		showHistory = true;
	} else {
		showHistory = false;
	}

	let history = [];
	let status = null;

	$: if (history && history.length > 0) {
		status = history.at(-1);
	}

	$: if (!equal(statusHistory, history)) {
		history = statusHistory;
	}

	/* One job each: the rail above says who is working and for how long; this
	   line only says what is happening, in words. It keeps pace with the rail:
	   while the rail's light travels to the next agent the line says so, and
	   that agent's words start as the light lands. Once the run is over it is
	   one quiet line into the full history. */
	$: handover = status?.done === false && FOURCE_ACTIONS.has(status?.action) ? rail?.handover ?? null : null;
	$: summary =
		status?.done === true && rail?.inChain
			? {
					steps: history.length,
					worked: rail.worked,
					// A run that failed or was stopped says so, not how long it worked.
					stopped: rail.outcome === 'interrupted' || ['error', 'stopped'].includes(status?.action)
				}
			: null;
	const passingTo = (name) => (name === 'You' ? 'you for sign-off' : name);
	// A change of stage crosses the line over; a new line within a stage is
	// LiveStatusLine's own roll.
	$: lineKey = handover ? `h:${handover.to}` : summary ? 'end' : `l:${rail?.stage ?? ''}`;

</script>

{#if history && history.length > 0}
	{#if status?.hidden !== true}
		<!-- Once the run is over the line is a quiet way into the full history,
		     at the size of the fold-outs under the answer, with room below. -->
		<div
			class="{status?.done === true
				? 'mb-2 text-[13.5px]'
				: 'text-[0.9375rem]'} flex flex-col w-full transition-[font-size,margin] duration-300"
		>
			<button
				class="w-full"
				aria-label={$i18n.t('Toggle status history')}
				aria-expanded={showHistory}
				on:click={() => {
					showHistory = !showHistory;
				}}
			>
				<!-- Both lines share one grid cell while they cross, so nothing below
				     moves. The old line leaves first; the new one follows. -->
				<div class="grid min-w-0">
					{#key lineKey}
						<div
							class="[grid-area:1/1] flex min-w-0 items-center"
							in:fly={{ y: reduced ? 0 : 6, duration: reduced ? 0 : 450, delay: reduced ? 0 : 340, opacity: 0 }}
							out:fly={{ y: reduced ? 0 : -6, duration: reduced ? 0 : 320, opacity: 0 }}
						>
							{#if handover}
								<span class="truncate text-[0.9375rem] text-gray-600 dark:text-gray-400"
									>Passing to {passingTo(handover.to)}…</span
								>
							{:else if summary}
								<!-- The whole run in one line; the chevron turns as the history
								     opens below it. -->
								<span
									class="inline-flex items-center gap-1 text-gray-600 transition-colors duration-200 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
								>
									{#if summary.stopped}
										Stopped after {summary.steps} {summary.steps === 1 ? 'step' : 'steps'}
									{:else}
										{summary.steps}
										{summary.steps === 1 ? 'step' : 'steps'}{#if summary.worked}&nbsp;in {summary.worked}{/if}
									{/if}
									<svg
										class="size-3 transition-transform duration-300 ease-out {showHistory ? 'rotate-90' : ''}"
										viewBox="0 0 12 12"
										fill="none"
										stroke="currentColor"
										stroke-width="1.5"
										stroke-linecap="round"
										stroke-linejoin="round"
										aria-hidden="true"><path d="M4.5 2.5 8 6l-3.5 3.5" /></svg
									>
								</span>
							{:else}
								<!-- 4CE's own stages get the rolling line; upstream statuses (web
								     and knowledge search) keep their own rendering. The expanded
								     history below always lists the factual statuses. -->
								<div class="min-w-0 flex-1">
									{#if FOURCE_ACTIONS.has(status?.action)}
										<LiveStatusLine {status} />
									{:else}
										<StatusItem {status} />
									{/if}
								</div>
							{/if}
						</div>
					{/key}
				</div>
			</button>

			{#if showHistory}
				<div class="flex flex-row">
					{#if history.length > 1}
						<div class="w-full mt-1">
							{#each history as status, idx}
								<div class="flex items-stretch gap-2.5 mb-1">
									<div class="shrink-0 w-3.5 flex flex-col items-center">
										<div class="pt-3 mb-1.5">
											<span class="relative flex size-1.5 rounded-full justify-center items-center">
												<span
													class="relative inline-flex size-1.5 rounded-full bg-gray-400/70 dark:bg-gray-500/70"
												></span>
											</span>
										</div>
										{#if idx !== history.length - 1}
											<div
												class="w-px h-[calc(100%-14px)] bg-gradient-to-b from-gray-300/80 to-gray-200/40 dark:from-gray-700 dark:to-gray-800"
											/>
										{/if}
									</div>

									<StatusItem {status} done={true} />
								</div>
							{/each}
						</div>
					{/if}
				</div>
			{/if}
		</div>
	{/if}
{/if}
