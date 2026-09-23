<script lang="ts">
	/*
	 * One pass of one agent, as a row in the Overview's column: FRIDAY, JARVIS,
	 * ULTRON, then again from FRIDAY whenever ULTRON sends the work back, and
	 * the human gate last. Named and coloured as on the stage rail in the chat;
	 * clicking it opens the answer it belongs to.
	 */
	import { Handle, Position, type NodeProps } from '@xyflow/svelte';
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	type $$Props = NodeProps;
	export let data: $$Props['data'];

	$: agent = data?.agent ?? {};
	$: gate = agent.name === 'YOU';
	$: name = gate ? $i18n.t('You') : agent.name;
	// The gate's time is how long the reviewer took, so it says "waited".
	$: detail = agent.model ?? (gate ? '' : agent.role);
</script>

<div
	class="ov-agent group box-border flex h-11 w-60 items-center gap-2 rounded-2xl border px-2.5 transition-[border-color,opacity,transform] duration-200 hover:-translate-y-px
		{agent.active
		? 'border-gray-900 bg-white dark:border-gray-100 dark:bg-gray-900'
		: 'border-gray-200/90 bg-white hover:border-gray-300 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-gray-700'}"
	style="--k: {data?.index ?? 0}"
>
	<span
		class="ov-agent-dot size-[6px] shrink-0 rounded-full {agent.active
			? 'active bg-gray-900 dark:bg-white'
			: gate
				? 'bg-gray-900 dark:bg-white'
				: agent.tone === 'good'
				? 'bg-emerald-500'
				: agent.tone === 'warn'
					? 'bg-amber-500'
					: 'bg-gray-400 dark:bg-gray-500'}"
		aria-hidden="true"
	></span>

	<span
		class="shrink-0 text-[10px] font-medium tracking-[0.08em] {gate
			? ''
			: 'uppercase'} text-gray-900 dark:text-gray-100">{name}</span
	>

	<!-- Which pass this is, when the work went round more than once. -->
	{#if agent.pass > 1}
		<span class="shrink-0 text-[10px] text-gray-400 dark:text-gray-500"
			>{$i18n.t('try')}
			{agent.pass}</span
		>
	{/if}

	<!-- The model gives way first when the row is tight; the time never does. -->
	<span class="ml-auto min-w-0 truncate text-right text-[10px] text-gray-500 dark:text-gray-400">
		{detail}
	</span>
	{#if agent.time}
		<span class="shrink-0 text-[10px] tabular-nums text-gray-500 dark:text-gray-400"
			>{gate && !agent.active ? `waited ${agent.time}` : agent.time}</span
		>
	{/if}

	{#if agent.note}
		<span
			class="shrink-0 text-[10px] font-medium {agent.active
				? 'shimmer'
				: gate
					? 'text-gray-700 dark:text-gray-200'
					: agent.tone === 'good'
					? 'text-emerald-700 dark:text-emerald-300'
					: agent.tone === 'warn'
						? 'text-amber-700 dark:text-amber-300'
						: 'text-gray-500'}">{agent.note}</span
		>
	{/if}

	<!-- `first` takes the wire straight down from the answer, or from the pass
	     above it; `chain` is kept for the sideways layout. -->
	<Handle
		type="target"
		id="first"
		position={data?.direction === 'horizontal' ? Position.Left : Position.Top}
		class="ov-handle"
	/>
	<Handle
		type="target"
		id="chain"
		position={data?.direction === 'horizontal' ? Position.Top : Position.Left}
		class="ov-handle"
	/>
	<Handle
		type="source"
		position={data?.direction === 'horizontal' ? Position.Right : Position.Bottom}
		class="ov-handle"
	/>
</div>

<style>
	/* The column unfolds out of its answer, pass after pass. */
	.ov-agent {
		animation: ov-agent-in 380ms calc(var(--k) * 70ms) cubic-bezier(0.2, 0.7, 0.2, 1) backwards;
	}
	.ov-agent-dot.active {
		animation: ov-agent-beat 1.1s ease-out infinite;
	}
	@keyframes ov-agent-in {
		from {
			opacity: 0;
			transform: translateY(-10px) scale(0.98);
		}
	}
	@keyframes ov-agent-beat {
		from {
			box-shadow: 0 0 0 0 rgba(120, 120, 130, 0.45);
		}
		to {
			box-shadow: 0 0 0 5px transparent;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.ov-agent,
		.ov-agent-dot.active {
			animation: none;
		}
	}
</style>
