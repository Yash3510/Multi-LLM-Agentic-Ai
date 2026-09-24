<script lang="ts">
	/**
	 * 4CE: the sovereignty page. What the workbench was observed connecting
	 * to, beside what its configuration permits - proof first, assurance
	 * second, and each said plainly for what it is.
	 */
	import { onDestroy, onMount } from 'svelte';
	import {
		getAudit,
		getEgress,
		resetEgress,
		runCanary,
		type Audit,
		type Egress
	} from '$lib/apis/fource';

	let egress: Egress | null = null;
	let audit: Audit | null = null;
	let loadError = '';
	let auditError = '';
	let canaryBusy = false;
	let canaryError = '';
	let timer: ReturnType<typeof setInterval>;

	const poll = async () => {
		try {
			egress = await getEgress(localStorage.token);
			loadError = '';
		} catch (err) {
			loadError = typeof err === 'string' ? err : 'The backend did not answer.';
		}
	};

	const loadAudit = async () => {
		try {
			audit = await getAudit(localStorage.token);
			auditError = '';
		} catch (err) {
			auditError = typeof err === 'string' ? err : 'The audit could not run.';
		}
	};

	const canary = async () => {
		canaryBusy = true;
		canaryError = '';
		try {
			await runCanary(localStorage.token);
		} catch (err) {
			canaryError = typeof err === 'string' ? err : 'The canary could not run.';
		}
		canaryBusy = false;
		poll();
	};

	const newWindow = async () => {
		egress = await resetEgress(localStorage.token).catch(() => egress);
	};

	onMount(() => {
		poll();
		loadAudit();
		timer = setInterval(poll, 1000);
	});
	onDestroy(() => clearInterval(timer));

	const clock = (epoch: number) =>
		new Date(epoch * 1000).toLocaleTimeString([], {
			hour: '2-digit',
			minute: '2-digit',
			second: '2-digit'
		});
	const span = (seconds: number) => {
		const s = Math.max(0, Math.round(seconds));
		if (s < 90) return `${s} s`;
		const m = Math.round(s / 60);
		return m < 90 ? `${m} min` : `${Math.floor(s / 3600)} h ${Math.round((s % 3600) / 60)} min`;
	};
	const plural = (n: number, one: string, many = `${one}s`) =>
		`${n.toLocaleString()} ${n === 1 ? one : many}`;

	const ROLE_ORDER = ['backend', 'model server', 'frontend'];
	const KIND = {
		local: { word: 'loopback', tone: 'text-gray-500 dark:text-gray-400' },
		lan_in: { word: 'LAN, inbound', tone: 'text-gray-500 dark:text-gray-400' },
		lan_expected: { word: 'LAN, configured endpoint', tone: 'text-gray-500 dark:text-gray-400' },
		lan_out: { word: 'LAN, outbound', tone: 'text-amber-700 dark:text-amber-400' },
		external: { word: 'internet', tone: 'text-amber-700 dark:text-amber-400 font-semibold' },
		canary: { word: 'canary', tone: 'text-gray-500 dark:text-gray-400' }
	};

	$: flows = egress?.flows;
	$: sampling = !!egress?.running && !egress?.error && egress.now - egress.last_sample < 5;
	$: external = flows?.external ?? 0;
	$: lanOut = flows?.lan_out ?? 0;
	$: clean = sampling && external === 0 && lanOut === 0;
	$: lastCanary = egress?.canaries?.[0];
	$: reached = [...(egress?.external ?? []), ...(egress?.lan_out ?? [])];
	$: roles = ROLE_ORDER.map((role) => ({
		role,
		members: (egress?.scope ?? []).filter((s) => s.role === role)
	})).filter((group) => group.members.length);
	// The processes that serve a port are the ones a firewall rule has to name.
	$: serving = (egress?.scope ?? []).filter((s) => s.listening.length && s.exe);
</script>

<div class="mx-auto w-full max-w-4xl px-4 pb-16 md:px-6">
	<header class="pt-2 pb-5">
		<h1 class="text-xl font-semibold text-gray-900 dark:text-white">Sovereignty</h1>
		<p class="mt-1 max-w-2xl text-sm text-gray-600 dark:text-gray-400">
			What the workbench was observed connecting to, and beside it what its configuration permits.
			The first is proof; the second is assurance.
		</p>
	</header>

	{#if loadError && !egress}
		<div
			class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-300"
		>
			{loadError}
		</div>
	{:else if egress}
		<!-- The verdict: one number, and exactly what it covers. -->
		<section
			class="rounded-2xl border p-5 {clean
				? 'border-emerald-200 dark:border-emerald-900/60'
				: sampling
					? 'border-amber-300 dark:border-amber-800'
					: 'border-dashed border-gray-300 dark:border-gray-700'}"
		>
			<div class="flex flex-wrap items-start justify-between gap-4">
				<div>
					<div class="text-xs uppercase tracking-[0.08em] text-gray-500 dark:text-gray-400">
						Observed · this window
					</div>
					<div class="mt-1 flex items-baseline gap-2">
						<span
							class="text-5xl font-semibold tabular-nums {clean
								? 'text-gray-900 dark:text-white'
								: sampling
									? 'text-amber-700 dark:text-amber-400'
									: 'text-gray-400'}">{sampling ? external : '—'}</span
						>
						<span class="text-base text-gray-700 dark:text-gray-300"
							>{sampling ? `external connection${external === 1 ? '' : 's'}` : 'not observed'}</span
						>
					</div>
					<p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
						{#if sampling}
							From {plural(egress.scope.length, 'workbench process', 'workbench processes')} over the
							last
							{span(egress.now - egress.since)} · {egress.samples.toLocaleString()} samples, one every
							{egress.interval_ms} ms · since {clock(egress.since)}
						{:else if egress.error}
							The watch reported an error: {egress.error}
						{:else}
							The egress watch is not sampling, so nothing here is evidence. It starts with the 4CE
							backend.
						{/if}
					</p>
				</div>
				<div class="flex flex-col items-start gap-2 sm:items-end">
					<button
						class="rounded-full bg-gray-900 px-4 py-1.5 text-sm font-medium text-white transition hover:bg-gray-800 disabled:opacity-50 dark:bg-white dark:text-gray-900 dark:hover:bg-gray-100"
						disabled={canaryBusy || !sampling}
						on:click={canary}
					>
						{canaryBusy ? 'Trying…' : 'Run the canary'}
					</button>
					<button
						class="text-xs text-gray-500 underline-offset-2 hover:underline dark:text-gray-400"
						on:click={newWindow}
						title="Clears the counts and starts observing afresh - at the start of a demo, say"
					>
						Start a new window
					</button>
				</div>
			</div>

			<div class="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-5">
				{#each [{ label: 'Loopback', value: flows?.local ?? 0, warn: false }, { label: 'LAN, inbound', value: flows?.lan_in ?? 0, warn: false }, { label: 'LAN, configured', value: flows?.lan_expected ?? 0, warn: false }, { label: 'LAN, other outbound', value: lanOut, warn: lanOut > 0 }, { label: 'Internet', value: external, warn: external > 0 }] as tile}
					<div
						class="rounded-xl px-3 py-2 {tile.warn
							? 'bg-amber-50 dark:bg-amber-950/40'
							: 'bg-gray-50 dark:bg-gray-850'}"
					>
						<div class="text-[11px] text-gray-600 dark:text-gray-400">{tile.label}</div>
						<div
							class="text-lg font-semibold tabular-nums {tile.warn
								? 'text-amber-800 dark:text-amber-300'
								: 'text-gray-900 dark:text-white'}"
						>
							{tile.value.toLocaleString()}
						</div>
					</div>
				{/each}
			</div>
			<p class="mt-2 text-xs text-gray-500 dark:text-gray-400">
				Counted as distinct connections. Loopback is the workbench talking to itself - the backend
				to the model server, the browser to the backend.
			</p>
		</section>

		<!-- The canary: the control demonstrated, not described. -->
		<section class="mt-6">
			<h2 class="text-sm font-semibold text-gray-900 dark:text-white">Canary</h2>
			<p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
				Tries to open a connection from the backend to <code class="text-xs"
					>{egress.canary_target}</code
				>
				- a handshake only, nothing sent. <b>Blocked</b> is what a sovereign host shows.
				<b>Reachable</b> means the workbench made no such call but nothing on this host prevents one.
			</p>
			{#if canaryError}
				<p class="mt-2 text-sm text-amber-700 dark:text-amber-400">{canaryError}</p>
			{/if}
			{#if lastCanary}
				<div
					class="mt-3 rounded-xl border px-4 py-3 {lastCanary.outcome === 'blocked'
						? 'border-emerald-200 dark:border-emerald-900/60'
						: 'border-amber-300 dark:border-amber-800'}"
				>
					<div class="flex flex-wrap items-baseline gap-x-2">
						<span
							class="text-sm font-semibold {lastCanary.outcome === 'blocked'
								? 'text-emerald-700 dark:text-emerald-400'
								: 'text-amber-700 dark:text-amber-400'}"
							>{lastCanary.outcome === 'blocked' ? 'Blocked' : 'Reachable'}</span
						>
						<span class="text-sm text-gray-700 dark:text-gray-300">— {lastCanary.detail}</span>
					</div>
					<div class="mt-1 text-xs text-gray-500 dark:text-gray-400">
						{clock(lastCanary.at)} · {lastCanary.ms} ms · logged, and not counted as an external connection
					</div>
				</div>
				{#if egress.canaries.length > 1}
					<ul class="mt-2 space-y-0.5 text-xs text-gray-500 dark:text-gray-400">
						{#each egress.canaries.slice(1, 6) as earlier}
							<li>{clock(earlier.at)} · {earlier.outcome} — {earlier.detail}</li>
						{/each}
					</ul>
				{/if}
			{:else}
				<p class="mt-3 text-sm text-gray-500 dark:text-gray-400">Not run in this window.</p>
			{/if}
		</section>

		{#if reached.length}
			<section class="mt-6">
				<h2 class="text-sm font-semibold text-amber-800 dark:text-amber-300">
					Seen leaving the machine
				</h2>
				<div class="mt-2 overflow-x-auto rounded-xl border border-amber-200 dark:border-amber-900">
					<table class="w-full text-left text-xs">
						<thead class="text-gray-500 dark:text-gray-400">
							<tr>
								<th class="px-3 py-2 font-medium">Process</th>
								<th class="px-3 py-2 font-medium">To</th>
								<th class="px-3 py-2 font-medium">State</th>
								<th class="px-3 py-2 font-medium">First seen</th>
								<th class="px-3 py-2 font-medium">Last seen</th>
							</tr>
						</thead>
						<tbody class="text-gray-800 dark:text-gray-200">
							{#each reached as event}
								<tr class="border-t border-amber-100 dark:border-amber-950">
									<td class="px-3 py-1.5"
										>{event.process} <span class="text-gray-500">({event.role})</span></td
									>
									<td class="px-3 py-1.5 font-mono">{event.remote}</td>
									<td class="px-3 py-1.5">{event.state.toLowerCase().replace('_', ' ')}</td>
									<td class="px-3 py-1.5 tabular-nums">{clock(event.first)}</td>
									<td class="px-3 py-1.5 tabular-nums">{clock(event.last)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</section>
		{/if}

		<!-- Scope: what "the workbench" means in the count above. -->
		<section class="mt-6">
			<h2 class="text-sm font-semibold text-gray-900 dark:text-white">Watched processes</h2>
			<div class="mt-2 grid gap-2 sm:grid-cols-3">
				{#each roles as group}
					<div class="rounded-xl bg-gray-50 px-3 py-2 dark:bg-gray-850">
						<div class="text-xs font-medium capitalize text-gray-700 dark:text-gray-300">
							{group.role}
						</div>
						<ul class="mt-1 space-y-0.5 text-xs text-gray-600 dark:text-gray-400">
							{#each group.members as member}
								<li>
									{member.process}
									<span class="tabular-nums text-gray-400">{member.pid}</span>
									{#if member.listening.length}
										<span class="text-gray-500">· :{member.listening.join(', :')}</span>
									{/if}
								</li>
							{/each}
						</ul>
					</div>
				{/each}
			</div>
		</section>

		<section class="mt-6">
			<h2 class="text-sm font-semibold text-gray-900 dark:text-white">Live connections</h2>
			<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
				The latest sample, refreshed every second.
			</p>
			{#if egress.live.length}
				<div class="mt-2 overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
					<table class="w-full text-left text-xs">
						<thead class="text-gray-500 dark:text-gray-400">
							<tr>
								<th class="px-3 py-2 font-medium">Process</th>
								<th class="px-3 py-2 font-medium">Local</th>
								<th class="px-3 py-2 font-medium">Remote</th>
								<th class="px-3 py-2 font-medium">State</th>
								<th class="px-3 py-2 font-medium">Where</th>
							</tr>
						</thead>
						<tbody class="text-gray-800 dark:text-gray-200">
							{#each egress.live as row}
								<tr class="border-t border-gray-100 dark:border-gray-850">
									<td class="px-3 py-1.5">{row.process}</td>
									<td class="px-3 py-1.5 font-mono text-gray-500">{row.local}</td>
									<td class="px-3 py-1.5 font-mono">{row.remote}</td>
									<td class="px-3 py-1.5">{row.state.toLowerCase().replace('_', ' ')}</td>
									<td class="px-3 py-1.5 {KIND[row.kind]?.tone ?? ''}"
										>{KIND[row.kind]?.word ?? row.kind}</td
									>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
					No open connections in the latest sample.
				</p>
			{/if}
		</section>

		<!-- Assurance: what the configuration permits, from the same code the chat audit runs. -->
		<section class="mt-8">
			<div class="flex items-baseline justify-between gap-2">
				<h2 class="text-sm font-semibold text-gray-900 dark:text-white">
					What the configuration permits
				</h2>
				<button
					class="text-xs text-gray-500 underline-offset-2 hover:underline dark:text-gray-400"
					on:click={loadAudit}>Re-run</button
				>
			</div>
			{#if auditError}
				<p class="mt-2 text-sm text-amber-700 dark:text-amber-400">{auditError}</p>
			{:else if audit}
				<p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
					{audit.passed} of {audit.total} configured surfaces pass.
				</p>
				<ul
					class="mt-2 divide-y divide-gray-100 rounded-xl border border-gray-200 dark:divide-gray-850 dark:border-gray-800"
				>
					{#each audit.checks as check}
						<li class="flex gap-3 px-3 py-1.5 text-xs">
							<span
								class="w-9 flex-none font-semibold {check.ok
									? 'text-emerald-700 dark:text-emerald-400'
									: 'text-amber-700 dark:text-amber-400'}">{check.ok ? 'PASS' : 'FAIL'}</span
							>
							<span class="w-48 flex-none text-gray-800 dark:text-gray-200">{check.label}</span>
							<span class="text-gray-600 dark:text-gray-400">{check.detail}</span>
						</li>
					{/each}
				</ul>
			{:else}
				<p class="mt-2 text-sm text-gray-500">Running the audit…</p>
			{/if}
		</section>

		<!-- Making it physical: the rule is the operator's to add; the canary shows it works. -->
		<section class="mt-8">
			<h2 class="text-sm font-semibold text-gray-900 dark:text-white">Making it physical</h2>
			<p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
				Observation shows what the workbench did. An egress rule on the host makes it unable to do
				otherwise - add one for each program below, then run the canary: it should read
				<b>Blocked</b>. Recipes for Windows and Linux are in
				<code class="text-xs">4ce/docs/HOW_TO_RUN.md</code>.
			</p>
			{#if serving.length}
				<ul class="mt-2 space-y-1 text-xs">
					{#each serving as member}
						<li class="text-gray-700 dark:text-gray-300">
							<span class="capitalize">{member.role}</span>
							<span class="text-gray-500">(:{member.listening.join(', :')})</span>
							<code class="ml-1 break-all text-gray-600 dark:text-gray-400">{member.exe}</code>
						</li>
					{/each}
				</ul>
			{/if}
		</section>

		<section class="mt-8 border-t border-gray-100 pt-4 dark:border-gray-850">
			<h2 class="text-xs font-semibold uppercase tracking-[0.06em] text-gray-500">
				What this cannot see
			</h2>
			<ul class="mt-2 list-disc space-y-1 pl-4 text-xs text-gray-500 dark:text-gray-400">
				{#each egress.limits as limit}
					<li>{limit}</li>
				{/each}
			</ul>
		</section>
	{/if}
</div>
