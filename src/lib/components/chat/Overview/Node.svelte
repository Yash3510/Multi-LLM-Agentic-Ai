<script lang="ts">
	/*
	 * An Overview card in the 4CE style: the bare mark (or the thinking orb
	 * while that answer is still being worked on), a clean preview of the
	 * text, and - for an agent-chain answer - the stage rail in miniature with
	 * how the run ended. The branch being read is outlined; branches left
	 * behind are dashed and dimmed.
	 */
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { Handle, Position, type NodeProps } from '@xyflow/svelte';
	import { getContext } from 'svelte';

	import ProfileImage from '../Messages/ProfileImage.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Heart from '$lib/components/icons/Heart.svelte';
	import LogoMotion from '$lib/components/common/LogoMotion.svelte';
	import { ALL_MOTIONS } from '$lib/components/common/logoMotion.js';
	import { user as currentUser } from '$lib/stores';
	import { getOutputText } from '../Messages/structuredOutput';
	import { runSummary, snippet, initials } from './summary';

	const i18n = getContext('i18n');

	type $$Props = NodeProps;
	export let data: $$Props['data'];

	const getMessageContent = (nodeData: any) =>
		getOutputText(nodeData?.message?.output) || nodeData?.message?.content || '';

	$: messageContent = getMessageContent(data);
	// A reply still being worked on has no text yet: say what it is doing.
	$: preview =
		snippet(messageContent) ||
		(data?.message?.done === false
			? (data?.message?.statusHistory?.at(-1)?.description ?? '…')
			: '');
	$: isUser = data?.message?.role === 'user';
	$: modelName = data?.model?.name ?? data?.message?.model ?? 'Assistant';
	$: is4ce = !isUser && /^4ce\b/i.test(modelName);
	$: summary = is4ce ? runSummary(data?.message) : null;
	$: personName = data?.user?.name ?? 'User';
	$: title = isUser
		? data?.user?.id && data.user.id === $currentUser?.id
			? $i18n.t('You')
			: personName
		: is4ce
			? '4CE'
			: modelName;
	/* Who worked on a 4CE answer, named as on the stage rail. A chain answer
	   lists the agents that ran - FRIDAY · JARVIS · ULTRON (TONY coordinates
	   every run, and four names do not fit the card); a direct reply is
	   TONY's alone. While the run is live, names appear as each agent is
	   reached, and the one working now is in ink. */
	$: agents = (summary?.stages ?? []).filter(
		(stage) => stage.reached && stage.name !== 'YOU' && (stage.name !== 'TONY' || !summary.chain)
	);
	// Several answers to one question, or several versions of one question.
	$: attempt =
		data?.siblings > 1 ? `${isUser ? $i18n.t('edit') : $i18n.t('try')} ${data.attempt}` : '';
	$: outcomeTone =
		summary?.outcome === 'released'
			? 'good'
			: ['withheld', 'stopped', 'failed', 'interrupted'].includes(summary?.outcome)
				? 'warn'
				: summary?.live
					? 'live'
					: 'quiet';
</script>

<div
	class="ov-card group relative box-border w-60 h-[5.75rem] rounded-xl border px-3 py-2.5 transition-[border-color,box-shadow,opacity,transform,background-color] duration-200 hover:-translate-y-px
		{data?.current
		? 'border-transparent bg-white ring-1 ring-gray-900 dark:bg-gray-900 dark:ring-gray-100'
		: data?.onPath
			? 'border-gray-200/90 bg-white hover:border-gray-300 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-gray-700'
			: 'border-dashed border-gray-300/80 bg-transparent opacity-60 hover:opacity-100 dark:border-gray-700'}"
	style="--lvl: {data?.level ?? 0}"
>
	<Tooltip
		content={data?.message?.error ? data.message.error.content : messageContent}
		class="w-full"
		allowHTML={false}
	>
		<div class="flex w-full gap-2.5">
			<div class="shrink-0 pt-px">
				{#if isUser}
					<span
						class="flex size-[18px] items-center justify-center rounded-full bg-gray-100 text-[8.5px] font-semibold tracking-wide text-gray-700 dark:bg-gray-800 dark:text-gray-200"
						aria-hidden="true">{initials(personName)}</span
					>
				{:else if is4ce}
					<span class="relative flex size-[18px] items-center justify-center" aria-hidden="true">
						{#if summary?.live}
							<!-- The same motions as the chat avatar (ResponseMessage). -->
							<LogoMotion motion={ALL_MOTIONS} randomStart size={17} />
						{:else}
							<img
								src="/static/logo-mark-dark.svg"
								class="ov-mark size-[17px] dark:hidden"
								alt=""
								draggable="false"
							/>
							<img
								src="/static/logo-mark-light.svg"
								class="ov-mark hidden size-[17px] dark:block"
								alt=""
								draggable="false"
							/>
						{/if}
					</span>
				{:else}
					<ProfileImage
						src={`${WEBUI_API_BASE_URL}/models/model/profile/image?id=${data.model?.id ?? data.message.model}&lang=${$i18n.language}`}
						className={'size-[18px]'}
					/>
				{/if}
			</div>

			<div class="min-w-0 flex-1">
				<div class="flex items-center justify-between gap-2">
					{#if agents.length}
						<div
							class="line-clamp-1 text-[10.5px] font-medium uppercase tracking-[0.05em]"
							aria-label={agents.map((stage) => stage.name).join(', ')}
						>
							{#each agents as stage, i (stage.name)}{#if i > 0}<span
										class="mx-1 text-gray-300 dark:text-gray-600">·</span
									>{/if}<span
									class={stage.active
										? 'ov-now text-gray-900 dark:text-white'
										: 'text-gray-700 dark:text-gray-200'}>{stage.name}</span
								>{/each}
						</div>
					{:else}
						<div class="line-clamp-1 text-xs font-medium text-gray-900 dark:text-gray-100">
							{title}
						</div>
					{/if}

					{#if attempt}
						<span class="ml-auto shrink-0 text-[10.5px] text-gray-400 dark:text-gray-500"
							>{attempt}</span
						>
					{/if}

					{#if !isUser}
						<!-- A badge on the card's corner, clear of the names and the try
						     label: shown on hover, and kept once the message is a favourite. -->
						<button
							class="nodrag nopan absolute -right-2 -top-2 flex size-5 items-center justify-center rounded-full bg-white ring-1 ring-gray-200 dark:bg-gray-900 dark:ring-gray-700 {data
								?.message?.favorite
								? ''
								: 'opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100'}"
							aria-label={data?.message?.favorite
								? $i18n.t('Remove from favorites')
								: $i18n.t('Add to favorites')}
							on:click={() => {
								data.message.favorite = !(data?.message?.favorite ?? false);
							}}
						>
							<Heart
								className="size-3 {data?.message?.favorite
									? 'fill-red-500 stroke-red-500'
									: 'text-gray-400 hover:fill-red-500 hover:stroke-red-500'}"
								strokeWidth="2.5"
							/>
						</button>
					{/if}
				</div>

				{#if data?.message?.error}
					<div class="mt-0.5 line-clamp-2 text-[11px] leading-snug text-red-500">
						{data.message.error.content}
					</div>
				{:else}
					<div
						class="mt-0.5 text-[11px] leading-snug text-gray-500 dark:text-gray-400 {summary
							? 'line-clamp-1'
							: 'line-clamp-2'}"
					>
						{preview}
					</div>
				{/if}

				{#if summary}
					<div class="mt-1.5 flex items-center gap-2">
						{#if summary.chain}
							<!-- The stage rail in miniature - TONY, FRIDAY, JARVIS, ULTRON, you -
							     drawn as a rib: the dots are joined, so a card reads as a run
							     rather than a row of specks, and the map reads as a tree. -->
							<span class="ov-rib flex shrink-0 items-center" aria-hidden="true">
								{#each summary.stages as stage, i (stage.name)}
									{#if i > 0}
										<span
											class="ov-seg {summary.stages[i - 1].reached && stage.reached
												? 'done'
												: summary.stages[i - 1].reached
													? 'live'
													: 'future'}"
										></span>
									{/if}
									<span
										class="ov-dot size-[5px] rounded-full {stage.active
											? 'active bg-gray-900 dark:bg-white'
											: stage.name === 'YOU' && stage.reached
												? 'bg-gray-900 dark:bg-white'
												: stage.reached
													? 'bg-gray-400 dark:bg-gray-500'
													: 'border border-gray-300 dark:border-gray-600'}"
										style="--i: {i}"
									></span>
								{/each}
							</span>
						{/if}
						<span
							class="shrink-0 rounded-full px-1.5 text-[10px] font-medium leading-4 {outcomeTone === 'good'
								? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300'
								: outcomeTone === 'warn'
									? 'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300'
									: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300'}"
						>
							<span class={summary.live ? 'shimmer' : ''}>{summary.label}</span>
						</span>
						{#if summary.chain && data?.onToggle}
							<!-- Unfolds the answer into its passes, straight down beneath it.
							     An icon, not a word: with the rib and the outcome on the same
							     line, the label pushed the button out past the card's edge.
							     nodrag/nopan and stopPropagation keep it from also opening the
							     message or panning the map. -->
							<Tooltip content={data.expanded ? $i18n.t('Hide the agents') : $i18n.t('Show the agents')}>
								<button
									type="button"
									class="nodrag nopan ml-auto flex size-5 shrink-0 items-center justify-center rounded-full transition-colors
										{data.expanded
										? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
										: 'text-gray-500 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100'}"
									aria-expanded={data.expanded ? 'true' : 'false'}
									aria-label={data.expanded ? $i18n.t('Hide the agents') : $i18n.t('Show the agents')}
									on:click|stopPropagation={() => data.onToggle()}
								>
									<svg
										class="size-2.5 transition-transform duration-300 {data.expanded ? 'rotate-180' : ''}"
										viewBox="0 0 16 16"
										fill="none"
										stroke="currentColor"
										stroke-width="2"
										aria-hidden="true"><path d="M3 6l5 5 5-5" /></svg
									>
								</button>
							</Tooltip>
						{/if}
					</div>
				{/if}
			</div>
		</div>
	</Tooltip>
	<Handle
		type="target"
		position={data?.direction === 'horizontal' ? Position.Left : Position.Top}
		class="ov-handle"
	/>
	<Handle
		type="source"
		position={data?.direction === 'horizontal' ? Position.Right : Position.Bottom}
		class="ov-handle"
	/>
	<!-- Where the agent lane attaches when the card is unfolded. -->
	<Handle
		type="source"
		id="lane"
		position={data?.direction === 'horizontal' ? Position.Bottom : Position.Right}
		class="ov-handle"
	/>
</div>

<style>
	/* Cards rise in by depth when the map opens, and a new message's card
	   rises in when it arrives. */
	.ov-card {
		animation: ov-in 420ms calc(var(--lvl) * 55ms) cubic-bezier(0.2, 0.7, 0.2, 1) backwards;
	}
	/* Its stage dots fill in after it, one by one. */
	.ov-dot {
		animation: ov-dot 280ms calc(var(--lvl) * 55ms + 220ms + var(--i) * 45ms)
			cubic-bezier(0.3, 1.4, 0.5, 1) backwards;
	}
	/* The stage still running beats softly. */
	/* The rib: hairline segments between the stage dots. A segment behind the
	   live stage carries a slow pulse, the same idea as the chat's wires. */
	.ov-seg {
		width: 8px;
		height: 1px;
		flex: none;
		margin: 0 2px;
		background: var(--color-gray-300, #d4d4d4);
	}
	:global(.dark) .ov-seg {
		background: var(--color-gray-700, #404040);
	}
	.ov-seg.done {
		background: var(--color-gray-400, #a3a3a3);
	}
	:global(.dark) .ov-seg.done {
		background: var(--color-gray-600, #525252);
	}
	.ov-seg.future {
		background: repeating-linear-gradient(90deg, currentColor 0 2px, transparent 2px 4px);
		color: var(--color-gray-300, #d4d4d4);
	}
	:global(.dark) .ov-seg.future {
		color: var(--color-gray-700, #404040);
	}
	.ov-seg.live {
		background: linear-gradient(90deg, var(--color-gray-400, #a3a3a3) 40%, transparent 40%);
		background-size: 8px 1px;
		animation: ov-rib-flow 1.1s linear infinite;
	}
	:global(.dark) .ov-seg.live {
		background: linear-gradient(90deg, var(--color-gray-500, #737373) 40%, transparent 40%);
		background-size: 8px 1px;
	}
	@keyframes ov-rib-flow {
		to {
			background-position: 8px 0;
		}
	}
	.ov-dot.active {
		animation:
			ov-dot 280ms calc(var(--lvl) * 55ms + 220ms + var(--i) * 45ms) cubic-bezier(0.3, 1.4, 0.5, 1)
				backwards,
			ov-beat 1.1s 600ms ease-out infinite;
	}
	/* The agent at work, named in the title, breathes with its dot. */
	.ov-now {
		animation: ov-now 1.6s ease-in-out infinite;
	}
	@keyframes ov-now {
		50% {
			opacity: 0.55;
		}
	}

	/* The mark turns a third of a circle on hover: it has three-fold symmetry,
	   so it lands exactly as it started. */
	.ov-mark {
		transition: transform 700ms cubic-bezier(0.3, 1.25, 0.5, 1);
	}
	.group:hover .ov-mark {
		transform: rotate(120deg);
	}

	@keyframes ov-in {
		from {
			opacity: 0;
			transform: translateY(6px) scale(0.985);
		}
	}
	@keyframes ov-dot {
		from {
			opacity: 0;
			scale: 0.2;
		}
	}
	@keyframes ov-beat {
		from {
			box-shadow: 0 0 0 0 rgba(120, 120, 130, 0.45);
		}
		to {
			box-shadow: 0 0 0 5px transparent;
		}
	}

	@media (prefers-reduced-motion: reduce) {
		.ov-card,
		.ov-dot,
		.ov-dot.active,
		.ov-now {
			animation: none;
		}
		.ov-mark {
			transition: none;
		}
	}
</style>
