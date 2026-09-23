<script lang="ts">
	/*
	 * The audit record of one 4CE run, opened from the receipt's "Audit" pill:
	 * how it ended, every step in order with its model and time (the send-back
	 * and the replan included), what it stood on, and its fingerprint - with a
	 * box that checks a pasted copy against it. Everything comes from the
	 * receipt the orchestrator wrote (`_receipt()` in
	 * 4ce/functions/orchestrator.py); nothing here leaves the machine.
	 */
	import Modal from '$lib/components/common/Modal.svelte';

	export let show = false;
	export let data: Record<string, any>;

	const TONE_DOT = {
		plain: 'bg-gray-400 dark:bg-gray-500',
		warn: 'bg-amber-500',
		good: 'bg-emerald-500',
		ink: 'bg-gray-900 dark:bg-white',
		faint: 'bg-gray-300 dark:bg-gray-600'
	};
	type Row = { name: string; text: string; model?: string; time?: string; tone: keyof typeof TONE_DOT };

	$: sources = (data.sources ?? []) as string[];
	$: cited = new Set<number>(data.cited ?? []);
	$: revision = data.revision;
	$: approval = data.approval ?? '';
	$: outcome =
		approval === 'approved' || approval === 'not required'
			? { word: 'Released', tone: 'text-emerald-700 dark:text-emerald-400' }
			: approval === 'rejected'
				? { word: 'Withheld', tone: 'text-amber-700 dark:text-amber-400' }
				: { word: 'Not released', tone: 'text-amber-700 dark:text-amber-400' };
	$: finished = data.at ? new Date(data.at) : null;
	$: when = finished
		? finished.toLocaleString(undefined, { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
		: '';

	const clip = (text: string, n = 90) => (text && text.length > n ? text.slice(0, text.lastIndexOf(' ', n)) + '…' : text);

	/* The chain, told as a list: TONY's routing, each agent's step (a second
	   try marked, the replan between the tries), then the human decision. */
	$: rows = ((): Row[] => {
		const routed = `Classified it as a ${data.task ?? 'general'} task${data.signals?.length ? ` · signals: ${data.signals.join(', ')}` : ''}`;
		const list: Row[] = (data.steps ?? []).some((step) => step.agent === 'TONY')
			? []
			: [{ name: 'TONY', text: routed, tone: 'plain' }];
		if (!data.steps) {
			list.push({
				name: '—',
				text: 'This answer predates step-by-step records; its execution timeline, under the answer, lists the steps',
				tone: 'faint'
			});
		}
		let replanned = false;
		for (const step of data.steps ?? []) {
			const label: string = step.label ?? '';
			const again = /attempt\s*2/.test(label);
			if (again && !replanned) {
				replanned = true;
				list.push({ name: 'TONY', text: 'Replanned, with the objections attached for FRIDAY and JARVIS', tone: 'faint' });
			}
			const tries = again ? ' · try 2' : '';
			const time = step.seconds ? `${Number(step.seconds).toFixed(1)}s` : '';
			if (step.agent === 'TONY') {
				list.push({ name: 'TONY', text: /classif/i.test(label) ? routed : label, model: step.model, time, tone: 'plain' });
			} else if (step.agent === 'FRIDAY') {
				list.push({ name: 'FRIDAY', text: `Analysed the request${sources.length ? ` against ${sources.length} retrieved ${sources.length === 1 ? 'source' : 'sources'}` : ''}${tries}`, model: step.model, time, tone: 'plain' });
			} else if (step.agent === 'JARVIS') {
				list.push({
					name: 'JARVIS',
					text: again ? `Revised the answer${revision ? ` · ${(revision.changes?.length ?? 0) + (revision.more ?? 0)} edits` : ''}` : 'Drafted the answer',
					model: step.model,
					time,
					tone: 'plain'
				});
			} else if (step.agent === 'ULTRON') {
				const failed = /FAIL/.test(label);
				const why = !again && failed && revision?.objections?.[0]?.text ? `: ${clip(revision.objections[0].text)}` : '';
				list.push({
					name: 'ULTRON',
					text: failed ? `Sent it back${why}` : /PASS/.test(label) ? 'Passed it' : 'Checked it',
					model: step.model,
					time,
					tone: failed ? 'warn' : /PASS/.test(label) ? 'good' : 'plain'
				});
			} else {
				list.push({ name: step.agent, text: `${label.replace(/\s*\(attempt\s*\d\)/, '')}${tries}`, model: step.model, time, tone: 'plain' });
			}
		}
		list.push({
			name: 'YOU',
			text:
				approval === 'approved'
					? `Released it${data.approver ? ` · ${data.approver}` : ''}`
					: approval === 'rejected'
						? 'Withheld it'
						: approval === 'not required'
							? 'Released without a sign-off (none required)'
							: 'No reviewer answered; not released',
			time: data.approved_at ?? '',
			tone: approval === 'approved' ? 'ink' : 'warn'
		});
		return list;
	})();

	/* Verify: the SHA-256 of a pasted copy against the released answer's. A
	   copy made with the answer's copy button ends where the answer ends; a
	   trailing rule or blank lines are not part of it. */
	let pasted = '';
	let verdict: '' | 'match' | 'differs' | 'empty' | 'unavailable' = '';
	const verify = async () => {
		// Answers from before the report became a card end with its line.
		let text = pasted.replace(/\r\n/g, '\n').trim();
		for (let before = ''; before !== text; ) {
			before = text;
			text = text
				.replace(/\n+\s*(?:-{3,}|\*{3,})\s*$/, '')
				.replace(/\n+\*\*Word report\*\*[^\n]*$/, '')
				.trim();
		}
		if (!text) {
			verdict = 'empty';
			return;
		}
		if (!crypto?.subtle) {
			verdict = 'unavailable';
			return;
		}
		const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
		const hex = [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
		verdict = hex === data.fingerprint ? 'match' : 'differs';
	};

	const summary = () =>
		[
			`4CE audit record${when ? ` · ${when}` : ''}`,
			`Outcome: ${outcome.word}${data.approver ? ` by ${data.approver}` : ''} · tries: ${data.attempts ?? 1} · external calls: ${data.external_calls ?? 0} · working time: ${data.seconds ?? '?'}s`,
			...rows.map((row) => `- ${row.name}: ${row.text}${row.model ? ` (${row.model})` : ''}${row.time ? ` · ${row.time}` : ''}`),
			sources.length ? `Sources: ${sources.map((name, i) => `[${i + 1}] ${name}${cited.has(i + 1) ? ' (cited)' : ''}`).join('; ')}` : 'Sources: none',
			data.fingerprint ? `Fingerprint (SHA-256 of the released answer): ${data.fingerprint}` : ''
		]
			.filter(Boolean)
			.join('\n');

	let copied = false;
	const copySummary = async () => {
		try {
			await navigator.clipboard.writeText(summary());
			copied = true;
			setTimeout(() => (copied = false), 1500);
		} catch {
			// Clipboard refused; the export still works.
		}
	};
	const exportJson = () => {
		const blob = new Blob([JSON.stringify({ kind: '4ce-audit-record', ...data }, null, 2)], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = url;
		link.download = `4ce-audit-${(data.at ?? new Date().toISOString()).slice(0, 16).replace(/[:T]/g, '-')}.json`;
		link.click();
		setTimeout(() => URL.revokeObjectURL(url), 1000);
	};

	const pill =
		'inline-flex items-center gap-1.5 rounded-full border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-800 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-100 dark:hover:bg-gray-850';
</script>

<Modal size="lg" bind:show>
	<div class="px-5 pb-5 pt-4 text-gray-800 dark:text-gray-200">
		<div class="flex flex-wrap items-center gap-x-3 gap-y-2">
			<img src="/static/logo-mark-dark.svg" class="size-[22px] dark:hidden" alt="" />
			<img src="/static/logo-mark-light.svg" class="hidden size-[22px] dark:block" alt="" />
			<h2 class="text-base font-semibold text-gray-900 dark:text-white">Audit record</h2>
			{#if when}<span class="text-xs text-gray-400 dark:text-gray-500">{when}</span>{/if}
			<span class="ml-auto flex items-center gap-1.5">
				<button type="button" class={pill} on:click={exportJson}>
					<svg class="size-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 2.5v8M4.75 7.5 8 10.75 11.25 7.5M3 13.25h10" /></svg>
					Export JSON
				</button>
				<button type="button" class={pill} on:click={copySummary}>{copied ? 'Copied' : 'Copy summary'}</button>
				<button
					type="button"
					class="rounded-lg p-1.5 text-gray-500 transition hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-white"
					aria-label="Close the audit record"
					on:click={() => (show = false)}
				>
					<svg class="size-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8" /></svg>
				</button>
			</span>
		</div>

		<div class="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
			{#each [{ label: 'Outcome', value: outcome.word, tone: outcome.tone }, { label: 'Tries', value: data.attempts ?? 1, tone: '' }, { label: 'External calls', value: data.external_calls ?? 0, tone: '' }, { label: 'Working time', value: data.seconds ? `${data.seconds}s` : '—', tone: '' }] as kpi}
				<div class="rounded-[10px] bg-gray-50 px-3 py-2 dark:bg-gray-850">
					<div class="text-[10.5px] uppercase tracking-[0.06em] text-gray-500 dark:text-gray-400">{kpi.label}</div>
					<div class="text-sm font-semibold {kpi.tone || 'text-gray-900 dark:text-white'}">{kpi.value}</div>
				</div>
			{/each}
		</div>

		<div class="audit-section">Chain</div>
		<ol class="space-y-0.5">
			{#each rows as row, i}
				<li class="audit-row" style="--i: {i}">
					<span class="mt-[7px] size-[7px] shrink-0 rounded-full {TONE_DOT[row.tone]}" aria-hidden="true"></span>
					<span class="w-16 shrink-0 text-[10.5px] font-medium uppercase tracking-[0.08em] text-gray-900 dark:text-gray-100">{row.name}</span>
					<span
						class="min-w-0 flex-1 {row.tone === 'warn'
							? 'text-amber-700 dark:text-amber-400'
							: row.tone === 'good'
								? 'text-emerald-700 dark:text-emerald-400'
								: ''}"
						>{row.text}{#if row.model}<span class="text-gray-400 dark:text-gray-500">{' · ' + row.model}</span>{/if}</span
					>
					<span class="shrink-0 text-[11px] tabular-nums text-gray-400 dark:text-gray-500">{row.time || '—'}</span>
				</li>
			{/each}
		</ol>

		<div class="audit-section">Evidence</div>
		{#if sources.length}
			<ul class="space-y-1 text-[12.5px]">
				{#each sources as name, i}
					<li class="flex flex-wrap items-center gap-2">
						<span
							class="rounded-full border px-2 text-[11px] font-medium leading-[18px] {cited.has(i + 1)
								? 'border-gray-300 text-gray-900 dark:border-gray-600 dark:text-white'
								: 'border-dashed border-gray-200 text-gray-500 dark:border-gray-700 dark:text-gray-400'}"
							>[{i + 1}] {name}</span
						>
						<span class="text-gray-500 dark:text-gray-400">{cited.has(i + 1) ? 'cited in the answer' : 'retrieved, not cited'}</span>
					</li>
				{/each}
			</ul>
		{:else}
			<p class="text-[12.5px] text-gray-500 dark:text-gray-400">No documents were retrieved for this answer.</p>
		{/if}

		{#if data.fingerprint}
			<div class="audit-section">Integrity</div>
			<p class="text-[12.5px] text-gray-700 dark:text-gray-300">
				Fingerprint, the SHA-256 of the released answer; the Word report carries the same one:
				<code class="mt-1 block break-all rounded-lg bg-gray-50 px-2 py-1 font-mono text-[11.5px] text-gray-800 dark:bg-gray-850 dark:text-gray-200">{data.fingerprint}</code>
			</p>
			<form class="mt-2 flex gap-2" on:submit|preventDefault={verify}>
				<input
					class="min-w-0 flex-1 rounded-[10px] border border-gray-200 bg-transparent px-3 py-2 text-[12.5px] outline-none placeholder:text-gray-400 focus:border-gray-400 dark:border-gray-700 dark:focus:border-gray-500"
					placeholder="Paste a copy of the answer to check it has not been changed"
					bind:value={pasted}
					on:input={() => (verdict = '')}
				/>
				<button
					type="submit"
					class="shrink-0 rounded-full border border-gray-900 px-4 text-xs font-medium text-gray-900 transition hover:bg-gray-900 hover:text-white dark:border-white dark:text-white dark:hover:bg-white dark:hover:text-gray-900"
					>Verify</button
				>
			</form>
			{#if verdict}
				<p
					class="mt-1.5 text-[12px] {verdict === 'match'
						? 'text-emerald-700 dark:text-emerald-400'
						: 'text-amber-700 dark:text-amber-400'}"
					role="status"
				>
					{verdict === 'match'
						? 'Matches: this is the released answer, unchanged.'
						: verdict === 'differs'
							? "Doesn't match: this text differs from the answer that was released."
							: verdict === 'empty'
								? 'Paste the answer first.'
								: 'This browser can only check over a secure connection (https or localhost).'}
				</p>
			{/if}
		{/if}
	</div>
</Modal>

<style>
	.audit-section {
		margin: 1rem 0 0.375rem;
		font-size: 10.5px;
		font-weight: 500;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--color-gray-500, #6b7280);
	}
	.audit-row {
		display: flex;
		align-items: flex-start;
		gap: 0.625rem;
		padding: 0.2rem 0;
		font-size: 12.5px;
		line-height: 1.5;
		animation: audit-row-in 260ms calc(var(--i) * 35ms) ease-out backwards;
	}
	@keyframes audit-row-in {
		from {
			opacity: 0;
			translate: 0 2px;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.audit-row {
			animation: none;
		}
	}
</style>
