<script>
	import { createEventDispatcher } from 'svelte';
	import { getContext } from 'svelte';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	import { theme } from '$lib/stores';
	import { Controls, SvelteFlow, ControlButton } from '@xyflow/svelte';
	import AlignVertical from '$lib/components/icons/AlignVertical.svelte';
	import AlignHorizontal from '$lib/components/icons/AlignHorizontal.svelte';
	import Pin from '$lib/components/icons/Pin.svelte';
	import PinSlash from '$lib/components/icons/PinSlash.svelte';

	export let nodes;
	export let nodeTypes;
	export let edges;
	export let setLayoutDirection;
	export let pinned = false;
</script>

<!-- 4CE styling for the conversation map: a plain canvas (no dot grid), the
     stage rail's cut-line wires with a flow along the branch being read, and
     the controls as one pill like the message box. Scoped to .ov-4ce so no
     other flow in the app is touched. -->
<SvelteFlow
	class="ov-4ce"
	{nodes}
	{nodeTypes}
	{edges}
	fitView
	minZoom={0.001}
	colorMode={$theme.includes('dark')
		? 'dark'
		: $theme === 'system'
			? window.matchMedia('(prefers-color-scheme: dark)').matches
				? 'dark'
				: 'light'
			: 'light'}
	nodesConnectable={false}
	nodesDraggable={false}
	on:nodeclick={(e) => dispatch('nodeclick', e.detail)}
	on:edgeclick={(e) => dispatch('edgeclick', e.detail)}
	oninit={() => {
		console.log('Flow initialized');
	}}
>
	<Controls showLock={false} position="bottom-center" orientation="horizontal">
		<ControlButton
			on:click={() => (pinned = !pinned)}
			title={pinned ? $i18n.t('Viewport Pinned') : $i18n.t('Viewport Unpinned')}
		>
			{#if pinned}
				<Pin />
			{:else}
				<PinSlash />
			{/if}
		</ControlButton>
		<ControlButton on:click={() => setLayoutDirection('vertical')} title="Vertical Layout">
			<AlignVertical className="size-4" />
		</ControlButton>
		<ControlButton on:click={() => setLayoutDirection('horizontal')} title="Horizontal Layout">
			<AlignHorizontal className="size-4" />
		</ControlButton>
	</Controls>
</SvelteFlow>

<style>
	:global(.ov-4ce) {
		--xy-background-color: transparent;
		/* The library draws a separator on each control button (it bent into a
		   ")" on the round buttons) and a grey plate behind its attribution. */
		--xy-controls-button-border-color: transparent;
		--xy-attribution-background-color: transparent;
		--ov-wire: rgb(209 213 219);
		--ov-flow: rgb(17 24 39);
	}
	:global(.dark .ov-4ce),
	:global(.ov-4ce.dark) {
		--ov-wire: rgb(55 65 81);
		--ov-flow: rgb(243 244 246);
	}

	/* Cards are plain containers; the card draws its own border and ring. */
	:global(.ov-4ce .svelte-flow__node-custom) {
		background: transparent;
		border: 0;
		padding: 0;
		box-shadow: none;
	}
	:global(.ov-4ce .ov-handle) {
		opacity: 0;
		pointer-events: none;
	}

	/* Unfolding an answer re-lays the map: cards slide to their new places
	   rather than jumping. */
	:global(.ov-4ce .svelte-flow__node) {
		transition: transform 380ms cubic-bezier(0.2, 0.7, 0.2, 1);
	}
	:global(.ov-4ce .svelte-flow__node-agent) {
		background: transparent;
		border: 0;
		padding: 0;
		box-shadow: none;
	}
	/* Lane wires: soft ink between the agents that ran (the flow is only for
	   a run still going), faint toward an agent the run never reached. */
	:global(.ov-4ce .ov-lane.reached .svelte-flow__edge-path) {
		stroke: var(--ov-flow);
		opacity: 0.5;
	}
	:global(.ov-4ce .ov-lane.on-path .svelte-flow__edge-path) {
		opacity: 1;
	}
	:global(.ov-4ce .ov-lane.future .svelte-flow__edge-path) {
		opacity: 0.45;
	}

	/* The passes of an unfolded answer hang straight down its column on a
	   plain hairline - the order is the story, so the wire stays quiet. */
	:global(.ov-4ce .ov-edge.ov-pass .svelte-flow__edge-path) {
		stroke-dasharray: none;
		stroke-width: 1;
		opacity: 0.7;
	}
	:global(.ov-4ce .ov-edge.ov-pass.on-path .svelte-flow__edge-path) {
		stroke-dasharray: 4 3;
		opacity: 1;
	}
	/* ULTRON sent the work back: the wire into the next pass turns amber and
	   says so. */
	/* The "sent back" wire opens why: ULTRON's objection and what changed. */
	:global(.ov-4ce .svelte-flow__edge.ov-back),
	:global(.ov-4ce .svelte-flow__edge-label) {
		cursor: pointer;
	}
	:global(.ov-4ce .ov-edge.ov-pass.ov-back .svelte-flow__edge-path) {
		stroke: #d97706;
		stroke-dasharray: 3 3;
		opacity: 0.9;
	}
	:global(.ov-4ce .svelte-flow__edge-label) {
		padding: 0 5px;
		border-radius: 9999px;
		background: var(--ov-bg, #fff);
		color: #b45309;
		font-size: 9.5px;
		font-weight: 500;
		letter-spacing: 0.02em;
		line-height: 14px;
	}
	:global(.dark .ov-4ce .svelte-flow__edge-label) {
		background: var(--color-gray-900, #171717);
		color: #fbbf24;
	}

	/* Wires: short cuts, as on the stage rail. */
	:global(.ov-4ce .ov-edge .svelte-flow__edge-path) {
		stroke: var(--ov-wire);
		stroke-width: 1.5;
		stroke-dasharray: 4 3;
		stroke-linecap: butt;
	}
	/* The branch being read: ink, with the cuts flowing toward the current
	   message - the way the rail carries energy to the next stage. */
	:global(.ov-4ce .ov-edge.on-path .svelte-flow__edge-path) {
		stroke: var(--ov-flow);
		animation: ov-flow 900ms linear infinite;
	}
	@keyframes -global-ov-flow {
		to {
			stroke-dashoffset: -7;
		}
	}

	/* Controls: one pill, bottom centre. */
	:global(.ov-4ce .svelte-flow__controls) {
		display: flex;
		align-items: center;
		gap: 2px;
		padding: 3px;
		margin-bottom: 14px;
		border-radius: 9999px;
		border: 1px solid rgb(229 231 235);
		background: rgb(255 255 255 / 0.92);
		box-shadow:
			0 1px 2px -1px rgba(16, 24, 40, 0.06),
			0 8px 20px -12px rgba(16, 24, 40, 0.25);
		backdrop-filter: blur(6px);
	}
	:global(.dark .ov-4ce .svelte-flow__controls),
	:global(.ov-4ce.dark .svelte-flow__controls) {
		border-color: rgb(38 38 38);
		background: rgb(23 23 23 / 0.9);
	}
	:global(.ov-4ce .svelte-flow__controls-button) {
		width: 28px;
		height: 28px;
		padding: 6px;
		border: 0;
		border-radius: 9999px;
		background: transparent;
		color: rgb(107 114 128);
		transition:
			background-color 150ms,
			color 150ms;
	}
	:global(.ov-4ce .svelte-flow__controls-button:hover) {
		background: rgb(243 244 246);
		color: rgb(17 24 39);
	}
	:global(.dark .ov-4ce .svelte-flow__controls-button:hover),
	:global(.ov-4ce.dark .svelte-flow__controls-button:hover) {
		background: rgb(38 38 38);
		color: rgb(243 244 246);
	}
	:global(.ov-4ce .svelte-flow__controls-button svg) {
		max-width: 14px;
		max-height: 14px;
	}
	/* The library's own icons are filled shapes; the pin and layout icons are
	   outlines (fill="none"), which a blanket fill would turn solid. */
	:global(.ov-4ce .svelte-flow__controls-button svg:not([fill='none'])) {
		fill: currentColor;
	}
	:global(.ov-4ce .svelte-flow__attribution) {
		opacity: 0.35;
	}

	@media (prefers-reduced-motion: reduce) {
		:global(.ov-4ce .ov-edge.on-path .svelte-flow__edge-path) {
			animation: none;
		}
		:global(.ov-4ce .svelte-flow__node) {
			transition: none;
		}
	}
</style>
