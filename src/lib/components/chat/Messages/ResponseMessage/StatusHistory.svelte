<script>
	import { getContext } from 'svelte';
	const i18n = getContext('i18n');

	import StatusItem from './StatusHistory/StatusItem.svelte';
	import LiveStatusLine, { FOURCE_ACTIONS } from './StatusHistory/LiveStatusLine.svelte';
	import equal from 'fast-deep-equal';
	export let statusHistory = [];
	export let expand = false;

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

</script>

{#if history && history.length > 0}
	{#if status?.hidden !== true}
		<div class="text-[0.9375rem] flex flex-col w-full">
			<button
				class="w-full"
				aria-label={$i18n.t('Toggle status history')}
				aria-expanded={showHistory}
				on:click={() => {
					showHistory = !showHistory;
				}}
			>
				<div class="flex items-center gap-2.5">
					<!-- 10px wide: the dot centres on the same line as the stage rail's
					     dots above it (their centre is 5px in from the text edge). -->
					<div class="shrink-0 flex items-center justify-center w-2.5 h-5 -my-0.5">
						<span class="size-1.5 rounded-full bg-gray-400/80 dark:bg-gray-500/80"></span>
					</div>
					<!-- 4CE's own stages get the rolling line; upstream statuses (web and
					     knowledge search) keep their own rendering. The expanded history
					     below always lists the factual statuses. -->
					{#if FOURCE_ACTIONS.has(status?.action)}
						<LiveStatusLine {status} />
					{:else}
						<StatusItem {status} />
					{/if}
				</div>
			</button>

			{#if showHistory}
				<div class="flex flex-row">
					{#if history.length > 1}
						<div class="w-full mt-1">
							{#each history as status, idx}
								<div class="flex items-stretch gap-2.5 mb-1">
									<div class="shrink-0 w-2.5 flex flex-col items-center">
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
