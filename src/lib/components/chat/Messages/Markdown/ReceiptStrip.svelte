<script lang="ts">
	/*
	 * The receipt under a 4CE answer: where it ran, what it stood on, how it
	 * was checked and who released it, in one line - with the checks beneath:
	 * 4CE's own figure check, then ULTRON's. The orchestrator writes it as a
	 * ```4ce-receipt block of JSON (`_receipt()` in 4ce/functions/
	 * orchestrator.py); the full provenance table follows it, folded away.
	 */
	import RevisionCard from './RevisionCard.svelte';
	import AuditSheet from './AuditSheet.svelte';

	let showAudit = false;

	export let data: {
		model?: string;
		sources?: string[];
		cited?: number[];
		verdict?: string;
		failed_by?: string;
		attempts?: number;
		checks?: { kind: 'ok' | 'problem' | 'unverified'; text: string; by?: string }[];
		approval?: string;
		approver?: string;
		approved_at?: string;
		seconds?: number;
		external_calls?: number;
		fingerprint?: string;
		revision?: any;
		steps?: any[];
	};

	/* The fingerprint: SHA-256 of the released answer's exact text. Clicking
	   copies it, so a copy of the answer can be checked against the record. */
	let copied = false;
	const copyFingerprint = async () => {
		try {
			await navigator.clipboard.writeText(data.fingerprint ?? '');
			copied = true;
			setTimeout(() => (copied = false), 1600);
		} catch {
			// Clipboard refused (an insecure origin, say): the title still shows it.
		}
	};

	$: sources = data.sources ?? [];
	$: checks = data.checks ?? [];
	$: verdict = (data.verdict ?? '').toUpperCase();
	$: tries = (data.attempts ?? 1) > 1 ? ` after ${data.attempts} tries` : '';

	type Pill = { label: string; detail: string; tone: 'plain' | 'good' | 'warn' | 'muted'; title?: string };
	$: pills = [
		{ label: 'Local', detail: data.model ?? 'open-weight model', tone: 'plain' },
		sources.length
			? {
					label: 'Grounded',
					detail:
						data.cited && data.cited.length !== sources.length
							? `${sources.length} retrieved · ${data.cited.length} cited`
							: `${sources.length} source${sources.length > 1 ? 's' : ''}`,
					tone: 'plain',
					title: sources
						.map((name, i) => `${data.cited?.includes(i + 1) ? 'Cited' : 'Retrieved'}: ${name}`)
						.join('\n')
				}
			: { label: 'Not grounded', detail: 'no documents used', tone: 'muted' },
		verdict === 'PASS'
			? { label: 'Checked', detail: `ULTRON passed it${tries}`, tone: 'good' }
			: verdict === 'FAIL'
				? {
						label: 'Checked',
						detail:
							data.failed_by === '4CE'
								? `failed on a cited figure${tries}`
								: `ULTRON failed it${tries}`,
						tone: 'warn'
					}
				: { label: 'Not checked', detail: 'verification off', tone: 'muted' },
		data.approval === 'approved'
			? {
					label: 'Released',
					detail: [data.approver && `by ${data.approver}`, data.approved_at].filter(Boolean).join(', ') || 'by you',
					tone: 'good'
				}
			: data.approval === 'rejected'
				? { label: 'Withheld', detail: 'by the reviewer', tone: 'warn' }
				: data.approval === 'not required'
					? { label: 'Released', detail: 'no approval needed', tone: 'plain' }
					: { label: 'Not released', detail: 'no reviewer answered', tone: 'warn' },
		...(data.seconds ? [{ label: `${data.seconds}s`, detail: 'working', tone: 'plain' }] : []),
		{ label: `${data.external_calls ?? 0}`, detail: 'external calls', tone: 'plain' }
	] as Pill[];

	const TONE = {
		plain: 'border-gray-200 text-gray-600 dark:border-gray-800 dark:text-gray-300',
		good: 'border-emerald-200 text-emerald-800 dark:border-emerald-900 dark:text-emerald-300',
		warn: 'border-amber-200 text-amber-800 dark:border-amber-900 dark:text-amber-300',
		muted: 'border-dashed border-gray-200 text-gray-400 dark:border-gray-800 dark:text-gray-500'
	};
	const MARK = {
		ok: { glyph: 'M3.5 8.5l3 3 6-7', tone: 'text-emerald-600 dark:text-emerald-400', word: 'Checked' },
		problem: { glyph: 'M4.5 4.5l7 7M11.5 4.5l-7 7', tone: 'text-amber-600 dark:text-amber-400', word: 'Problem' },
		unverified: { glyph: 'M4 8h8', tone: 'text-gray-400 dark:text-gray-500', word: 'Could not verify' }
	};
</script>

<div class="receipt my-2 not-prose" role="group" aria-label="How this answer was produced">
	<div class="flex flex-wrap gap-1.5">
		{#each pills as pill, n}
			<span
				style="--n: {n}"
				class="receipt-pill inline-flex items-center gap-1 rounded-full border bg-white px-2 py-0.5 text-[11px] leading-4 dark:bg-gray-900 {TONE[
					pill.tone
				]}"
				title={pill.title}
			>
				<span class="font-medium">{pill.label}</span>
				<span class="opacity-75">{pill.detail}</span>
			</span>
		{/each}
		{#if data.fingerprint}
			<button
				type="button"
				style="--n: {pills.length}"
				class="receipt-pill inline-flex items-center gap-1 rounded-full border border-gray-200 bg-white px-2 py-0.5 text-[11px] leading-4 text-gray-600 transition hover:border-gray-300 hover:text-gray-900 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300 dark:hover:border-gray-700 dark:hover:text-white"
				title="SHA-256 of the released answer, {data.fingerprint}. The Word report carries the same fingerprint. Click to copy."
				on:click={copyFingerprint}
			>
				<span class="font-medium">{copied ? 'Copied' : 'Fingerprint'}</span>
				<span class="font-mono text-[10.5px] opacity-75">{data.fingerprint.slice(0, 8)}</span>
			</button>
		{/if}
		<!-- The whole run as a record: every step, the evidence, the fingerprint. -->
		<button
			type="button"
			style="--n: {pills.length + 1}"
			class="receipt-pill inline-flex items-center gap-1 rounded-full border border-gray-900 bg-white px-2 py-0.5 text-[11px] font-medium leading-4 text-gray-900 transition hover:bg-gray-900 hover:text-white dark:border-gray-200 dark:bg-gray-900 dark:text-gray-100 dark:hover:bg-white dark:hover:text-gray-900"
			aria-haspopup="dialog"
			on:click={() => (showAudit = true)}
		>
			<svg class="size-3" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 2.5h7l3 3v8H3z" /><path d="M5.5 8h5M5.5 10.5h3" /></svg>
			Audit
		</button>
	</div>

	{#if data.revision?.objections?.length}
		<div class="receipt-checks" style="--n: {pills.length + 2}">
			<RevisionCard revision={data.revision} />
		</div>
	{/if}

	{#if checks.length}
		<div
			class="receipt-checks mt-2.5 rounded-xl border border-gray-100 px-3 py-2 dark:border-gray-850"
			style="--n: {pills.length + 3}"
		>
			<!-- 4CE's own mechanical check first, then ULTRON's; each line says
			     which of them made it. -->
			<div class="mb-1 text-[10.5px] font-medium uppercase tracking-[0.08em] text-gray-500 dark:text-gray-400">
				What was checked
			</div>
			<ul class="space-y-1">
				{#each checks as check, k}
					<li
						style="--k: {k}"
						class="receipt-check flex items-start gap-2 text-[12.5px] leading-snug text-gray-700 dark:text-gray-300">
						<svg
							class="mt-[3px] size-3 shrink-0 {MARK[check.kind]?.tone ?? MARK.unverified.tone}"
							viewBox="0 0 16 16"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
							aria-hidden="true"><path d={MARK[check.kind]?.glyph ?? MARK.unverified.glyph} /></svg
						>
						<span class="min-w-0 flex-1">
							<span class="sr-only">{MARK[check.kind]?.word ?? MARK.unverified.word}:</span>
							{check.text}
						</span>
						{#if check.by}
							<span
								class="mt-px shrink-0 text-[9.5px] font-medium uppercase tracking-[0.08em] text-gray-400 dark:text-gray-500"
								>{check.by}</span
							>
						{/if}
					</li>
				{/each}
			</ul>
		</div>
	{/if}
</div>


<AuditSheet bind:show={showAudit} {data} />

<style>
	/* When a run finishes in front of the reader, its receipt is set down
	   piece by piece: the pills in order, then the card of checks, line by
	   line. An answer opened later (no .message-in round it) is drawn still. */
	:global(.message-in) .receipt-pill {
		animation: receipt-in 300ms calc(var(--n) * 45ms) cubic-bezier(0.2, 0.7, 0.2, 1) backwards;
	}
	:global(.message-in) .receipt-checks {
		animation: receipt-in 360ms calc(var(--n) * 45ms) cubic-bezier(0.2, 0.7, 0.2, 1) backwards;
	}
	:global(.message-in) .receipt-check {
		animation: receipt-line 300ms calc(var(--k) * 60ms + 420ms) ease-out backwards;
	}
	@keyframes receipt-in {
		from {
			opacity: 0;
			translate: 0 3px;
		}
	}
	@keyframes receipt-line {
		from {
			opacity: 0;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		:global(.message-in) .receipt-pill,
		:global(.message-in) .receipt-checks,
		:global(.message-in) .receipt-check {
			animation: none;
		}
	}
</style>
