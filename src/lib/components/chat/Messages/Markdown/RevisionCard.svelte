<script lang="ts">
	/*
	 * What changed on try 2: when ULTRON (or 4CE's figure check) sent the first
	 * draft back, each objection is shown with the lines JARVIS changed for it
	 * and ULTRON's verdict on the revised draft. Every other edit is one click
	 * away. The orchestrator works the changes out (`_revision()` in
	 * 4ce/functions/orchestrator.py) and puts them in the receipt.
	 */
	export let revision: {
		objections: { text: string; by?: string; fixes: number[] }[];
		changes: { removed: string; added: string; kind: string }[];
		more?: number;
		by?: string;
		verdict?: string;
	};

	let showAll = false;

	$: changes = revision.changes ?? [];
	$: objections = revision.objections ?? [];
	$: passed = (revision.verdict ?? '') === 'PASS';
	$: fixed = new Set(objections.flatMap((objection) => objection.fixes ?? []));
	$: others = changes.length - fixed.size + (revision.more ?? 0);
	// The rest of the edits: the ones an objection points to are shown above.
	$: rest = changes.filter((_, i) => !fixed.has(i));
</script>

<div
	class="revision mt-2.5 rounded-xl border border-gray-200/80 px-3 py-2 dark:border-gray-800"
	role="group"
	aria-label="What changed on try 2"
>
	<div class="mb-1 flex items-center justify-between gap-3">
		<span class="text-[10.5px] font-medium uppercase tracking-[0.08em] text-gray-600 dark:text-gray-400"
			>What changed on try 2</span
		>
		<span
			class="text-[11px] font-medium {passed
				? 'text-emerald-700 dark:text-emerald-400'
				: 'text-amber-700 dark:text-amber-400'}"
			>{passed ? 'Passed on try 2' : 'Still failed on try 2'}</span
		>
	</div>

	{#each objections as objection}
		<div class="revision-row">
			<span class="revision-who">{objection.by ?? revision.by ?? 'ULTRON'} · try 1</span>
			<span class="text-gray-700 dark:text-gray-300">
				<span class="mr-1 font-semibold text-amber-700 dark:text-amber-400" aria-hidden="true">✕</span
				><span class="sr-only">Objection: </span>{objection.text}
			</span>
		</div>
		<div class="revision-row">
			<span class="revision-who">JARVIS · try 2</span>
			{#if objection.fixes?.length}
				<span class="flex flex-col items-start gap-1">
					{#each objection.fixes as i}
						{#if changes[i]?.removed}<del class="revision-del">{changes[i].removed}</del>{/if}
						{#if changes[i]?.added}<ins class="revision-ins">{changes[i].added}</ins>{/if}
					{/each}
				</span>
			{:else}
				<span class="text-gray-600 dark:text-gray-500"
					>No single change answers this one{others > 0 ? '; see every change below' : ''}.</span
				>
			{/if}
		</div>
	{/each}

	<div class="revision-row">
		<span class="revision-who">ULTRON · try 2</span>
		<span class="text-gray-700 dark:text-gray-300">
			{#if passed}
				<span class="mr-1 font-semibold text-emerald-700 dark:text-emerald-400" aria-hidden="true">✓</span>Passed the
				revised draft.
			{:else}
				<span class="mr-1 font-semibold text-amber-700 dark:text-amber-400" aria-hidden="true">✕</span>Failed the revised
				draft too; the reviewer saw that before deciding.
			{/if}
		</span>
	</div>

	{#if others > 0}
		<div
			class="mt-1 flex items-center justify-between gap-3 border-t border-gray-100 pt-1.5 text-[12px] text-gray-600 dark:border-gray-850 dark:text-gray-400"
		>
			<span>Also changed: {others} {others === 1 ? 'edit' : 'edits'}</span>
			<button
				type="button"
				class="rounded-full px-2 py-0.5 font-medium text-gray-900 transition hover:bg-gray-100 dark:text-gray-100 dark:hover:bg-gray-800"
				aria-expanded={showAll}
				on:click={() => (showAll = !showAll)}>{showAll ? 'Hide the changes' : 'Show every change'}</button
			>
		</div>
		{#if showAll}
			<ol class="revision-all mt-2 space-y-2 pb-1">
				{#each rest as change}
					<li
						class="flex flex-col items-start gap-1 border-l-2 border-gray-100 pl-2.5 text-[12.5px] leading-snug dark:border-gray-800"
					>
						{#if change.removed}<del class="revision-del">{change.removed}</del>{/if}
						{#if change.added}<ins class="revision-ins">{change.added}</ins>{/if}
					</li>
				{/each}
				{#if revision.more}
					<li class="text-[12px] text-gray-600 dark:text-gray-500">
						{revision.more} more {revision.more === 1 ? 'edit' : 'edits'}; both drafts are in the full provenance below
					</li>
				{/if}
			</ol>
		{/if}
	{/if}
</div>

<style>
	.revision-row {
		display: grid;
		grid-template-columns: 6.5rem minmax(0, 1fr);
		gap: 0.625rem;
		padding: 0.3rem 0;
		font-size: 12.5px;
		line-height: 1.5;
	}
	.revision-who {
		padding-top: 2px;
		font-size: 10px;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--color-gray-600, #676767);
	}
	:global(.dark) .revision-who {
		color: var(--color-gray-400, #b4b4b4);
	}
	.revision-del,
	.revision-ins {
		border-radius: 5px;
		padding: 0 5px;
		text-decoration: none;
	}
	.revision-del {
		background: rgb(254 242 242);
		color: rgb(185 28 28);
		text-decoration: line-through;
		text-decoration-color: rgb(185 28 28 / 0.45);
	}
	.revision-ins {
		background: rgb(236 253 245);
		color: rgb(4 120 87);
	}
	:global(.dark) .revision-del {
		background: rgb(127 29 29 / 0.3);
		color: rgb(252 165 165);
	}
	:global(.dark) .revision-ins {
		background: rgb(6 78 59 / 0.35);
		color: rgb(110 231 183);
	}
	.revision-all {
		animation: revision-open 220ms ease-out;
	}
	@keyframes revision-open {
		from {
			opacity: 0;
		}
	}
	@media (max-width: 480px) {
		.revision-row {
			grid-template-columns: minmax(0, 1fr);
			gap: 0.125rem;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.revision-all {
			animation: none;
		}
	}
</style>
