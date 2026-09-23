<script lang="ts">
	import { onMount, tick } from 'svelte';
	import {
		useSvelteFlow,
		useNodesInitialized,
		useStore,
		type Edge,
		type Node
	} from '@xyflow/svelte';

	import { writable } from 'svelte/store';
	import { models, user } from '$lib/stores';

	import '@xyflow/svelte/dist/style.css';

	import CustomNode from './Node.svelte';
	import AgentNode from './AgentNode.svelte';
	import { runSummary, agentRuns } from './summary';
	import Flow from './Flow.svelte';

	const { width, height } = useStore();

	const { fitView, fitBounds, setCenter } = useSvelteFlow();
	const nodesInitialized = useNodesInitialized();

	export let history;
	export let onNodeClick;
	export let chatUser = null;

	type LayoutDirection = 'vertical' | 'horizontal';
	type PositionMapEntry = {
		id: string;
		level: number;
		position: number;
		/* The drawn row: the depth in the conversation plus a row for every
		   unfolded answer above it, whose agents take a row of their own. */
		row: number;
	};

	/* The camera: never past 100%, so a single card is not blown up to fill
	   the panel (it opened at about 1.4x) and its neighbours stay in view.
	   Moving to another message glides rather than jumps. */
	const CAMERA = { maxZoom: 1, padding: 0.4 };
	const GLIDE = { ...CAMERA, duration: 450 };

	let selectedMessageId: string | null = null;
	let pinned = false;

	const nodes = writable<Node[]>([]);
	const edges = writable<Edge[]>([]);

	let layoutDirection: LayoutDirection = 'vertical';

	const nodeTypes = {
		custom: CustomNode,
		agent: AgentNode
	};

	/* Answers unfolded into their agents. A lane of agent cards sits to the
	   right of the answer - FRIDAY -> JARVIS -> ULTRON -> You - so the
	   conversation still runs straight down and no wire crosses it. */
	let expanded = new Set<string>();
	const PASS_GAP = 20; // between the rows of an unfolded answer, in px
	const BACK_GAP = 38; // before a pass that follows a failed check: room for "sent back"
	const isChainAnswer = (message: any) => {
		if (message?.role !== 'assistant') return false;
		const name = $models.find((model) => model.id === message.model)?.name ?? message.model ?? '';
		return /^4ce\b/i.test(name) && !!runSummary(message)?.chain;
	};
	// Where drawFlow put each card, so the camera can be aimed without waiting
	// for the flow to measure cards it has only just been given.
	const placed = new Map<string, { x: number; y: number; w: number; h: number }>();
	let fittedFor = '';
	/* An answer with its lane of agents, as one box for the camera. */
	const laneBounds = (id: string) => {
		const boxes = [...placed.entries()]
			.filter(([key]) => key === id || key.startsWith(`${id}::`))
			.map(([, box]) => box);
		if (!boxes.length) return null;
		const left = Math.min(...boxes.map((b) => b.x));
		const top = Math.min(...boxes.map((b) => b.y));
		const right = Math.max(...boxes.map((b) => b.x + b.w));
		const bottom = Math.max(...boxes.map((b) => b.y + b.h));
		return { x: left, y: top, width: right - left, height: bottom - top };
	};
	const onCurrentPath = (target: string) => {
		for (let id = history?.currentId; id && history.messages[id]; id = history.messages[id].parentId) {
			if (id === target) return true;
		}
		return false;
	};
	/* Frame whatever the reader is on: an unfolded answer with its whole lane,
	   otherwise the current card. */
	const refit = async (duration = 0) => {
		if (pinned) return;
		const open = [...expanded].find((id) => onCurrentPath(id));
		const bounds = open ? laneBounds(open) : null;
		if (!bounds) {
			await fitView({ nodes: [{ id: history.currentId }], ...CAMERA, duration });
			return;
		}
		// Framed by hand rather than with fitBounds: this flow version ignores
		// maxZoom there, and a short run was blown up to twice its size.
		const room = 1 - 2 * 0.07;
		const zoom = Math.min(
			CAMERA.maxZoom,
			($width * room) / bounds.width,
			($height * room) / bounds.height
		);
		await setCenter(bounds.x + bounds.width / 2, bounds.y + bounds.height / 2, { zoom, duration });
	};
	const toggleAgents = async (id: string) => {
		if (expanded.has(id)) expanded.delete(id);
		else expanded.add(id);
		expanded = expanded;
		await drawFlow(layoutDirection);
		const card = placed.get(id);
		if (!pinned && card) {
			await tick();
			if (expanded.has(id)) await refit(450);
			// Closing: back to the answer, at full size.
			else await setCenter(card.x + card.w / 2, card.y + card.h / 2, { zoom: 1, duration: 450 });
		}
	};

	/* First open: the newest answer comes already unfolded into its agents, so
	   the panel shows a run as a tree rather than a column of cards. After
	   that the reader's own choices stand. */
	let autoExpanded = false;
	$: if (history) {
		if (!autoExpanded && history.currentId && $models.length) {
			for (let id = history.currentId; id && history.messages[id]; id = history.messages[id].parentId) {
				if (isChainAnswer(history.messages[id])) {
					expanded.add(id);
					expanded = expanded;
					break;
				}
			}
			autoExpanded = true;
		}
		drawFlow(layoutDirection);
	}

	$: if (history && history.currentId && !pinned) {
		focusNode();
	}

	const focusNode = async () => {
		if (selectedMessageId === null) {
			await fitView({ nodes: [{ id: history.currentId }], ...GLIDE });
		} else {
			await fitView({ nodes: [{ id: selectedMessageId }], ...GLIDE });
		}

		selectedMessageId = null;
	};

	const drawFlow = async (direction: LayoutDirection) => {
		const nodeList: Node[] = [];
		const edgeList: Edge[] = [];
		placed.clear();
		const rootFontSize = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
		const nodeWidth = 15 * rootFontSize;
		// Matches the card's h-[5.75rem]: room for the stage strip under the preview.
		const nodeHeight = 5.75 * rootFontSize;
		const levelOffset = direction === 'vertical' ? nodeHeight + 70 : nodeWidth + 60;
		const siblingOffset = direction === 'vertical' ? nodeWidth + 60 : nodeHeight + 70;

		// A tidy tree: every card sits under its parent, and the answers (or
		// edits) that share a parent spread out centred beneath it. The row
		// counters used before put each card in the next free slot of its row,
		// so a follow-up to "try 2" was drawn under "try 1" with its wire
		// swooping across.
		const messages = history.messages;
		const kids = (id: string): string[] =>
			(messages[id]?.childrenIds ?? []).filter((child: string) => messages[child]);
		const span = new Map<string, number>();
		const measure = (id: string, seen = new Set<string>()): number => {
			if (seen.has(id)) return 1; // a malformed history must not loop forever
			seen.add(id);
			const children = kids(id);
			const base = children.length
				? children.reduce((sum, child) => sum + measure(child, seen), 0)
				: 1;
			// The agent rows sit in the answer's own column, so an unfolded
			// answer is no wider than a folded one.
			const width = base;
			span.set(id, width);
			return width;
		};
		// How many rows an unfolded answer's passes take up, so whatever follows
		// in the conversation starts below them.
		const passH = 2.75 * rootFontSize;
		// Where each pass sits below its answer, and how far the column runs.
		const passOffsets = (runs: { verdict: string | null }[]) => {
			let at = PASS_GAP;
			return runs.map((_, k) => {
				if (k > 0) at += passH + (runs[k - 1].verdict === 'FAIL' ? BACK_GAP : PASS_GAP);
				return at;
			});
		};
		const rowsTaken = (id: string) => {
			if (!expanded.has(id) || !isChainAnswer(messages[id])) return 0;
			const offsets = passOffsets(agentRuns(messages[id]));
			if (!offsets.length) return 0;
			return Math.ceil((offsets[offsets.length - 1] + passH + PASS_GAP) / levelOffset);
		};

		const positionMap = new Map<string, PositionMapEntry>();
		const place = (id: string, level: number, start: number, row: number) => {
			if (positionMap.has(id)) return;
			const children = kids(id);
			// An unfolded answer pushes what follows down a row, so its agents
			// have a row to branch into.
			const childRow = row + 1 + rowsTaken(id);
			let slot = start;
			for (const child of children) {
				place(child, level + 1, slot, childRow);
				slot += span.get(child) ?? 1;
			}
			const first = positionMap.get(children[0]);
			const last = positionMap.get(children[children.length - 1]);
			const position = first && last ? (first.position + last.position) / 2 : start;
			positionMap.set(id, { id, level, position, row });
		};
		let nextSlot = 0;
		for (const id of Object.keys(messages)) {
			if (!messages[id] || messages[messages[id].parentId]) continue; // roots only
			measure(id);
			place(id, 0, nextSlot, 0);
			nextSlot += span.get(id) ?? 1;
		}

		// The branch being read: the current message and every message above it.
		// Its cards are outlined and its wires carry the flow; the rest are dimmed.
		const onPath = new Set<string>();
		for (let id = history.currentId; id && history.messages[id]; id = history.messages[id].parentId) {
			onPath.add(id);
		}

		// Adjust positions based on siblings count to centralize vertical spacing
		Object.keys(history.messages).forEach((id) => {
			const pos = positionMap.get(id);
			if (!pos) return;

			const x = direction === 'vertical' ? pos.position * siblingOffset : pos.row * levelOffset;
			const y = direction === 'vertical' ? pos.row * levelOffset : pos.position * siblingOffset;

			placed.set(pos.id, { x, y, w: nodeWidth, h: nodeHeight });
			const parent = history.messages[history.messages[id].parentId];
			const siblings = parent?.childrenIds ?? [];
			nodeList.push({
				id: pos.id,
				type: 'custom',
				data: {
					user: chatUser ?? $user,
					message: history.messages[id],
					model: $models.find((model) => model.id === history.messages[id].model),
					direction,
					level: pos.level,
					onPath: onPath.has(id),
					current: id === history.currentId,
					siblings: siblings.length,
					attempt: siblings.indexOf(id) + 1,
					expanded: expanded.has(id),
					onToggle: isChainAnswer(history.messages[id]) ? () => toggleAgents(id) : null
				},
				position: { x, y }
			});

			// The passes: straight down the answer's own column - FRIDAY, JARVIS,
			// ULTRON, and round again whenever ULTRON sends the work back, with
			// the human gate last. The conversation carries on below them.
			if (expanded.has(id) && isChainAnswer(history.messages[id])) {
				const runs = agentRuns(history.messages[id]);
				const live = history.messages[id].done !== true;
				const offsets = passOffsets(runs);
				runs.forEach((agent, k) => {
					const down = (direction === 'vertical' ? y + nodeHeight : x + nodeWidth) + offsets[k];
					const at = direction === 'vertical' ? { x, y: down } : { x: down, y };
					placed.set(`${id}::${k}`, { ...at, w: nodeWidth, h: passH });
					nodeList.push({
						id: `${id}::${k}`,
						type: 'agent',
						data: { agent, index: k, direction, message: history.messages[id] },
						position: at
					});
					const from = k === 0 ? id : `${id}::${k - 1}`;
					// After a failed check the work goes round again: that wire says so.
					const sentBack = k > 0 && runs[k - 1].verdict === 'FAIL';
					edgeList.push({
						id: `${from}->${id}::${k}`,
						source: from,
						target: `${id}::${k}`,
						targetHandle: 'first',
						selectable: false,
						type: 'straight',
						label: sentBack ? 'sent back' : undefined,
						class: `ov-edge ov-pass${sentBack ? ' ov-back' : ''}${live ? ' on-path' : ''}`
					});
				});
			}

			// Create edges
			const parentId = history.messages[id].parentId;
			if (parentId) {
				// Cut-line wires, like the stage rail's: the branch being read
				// carries a flow toward the current message; the rest stay still.
				edgeList.push({
					id: parentId + '-' + pos.id,
					source: parentId,
					target: pos.id,
					selectable: false,
					class: onPath.has(id) && onPath.has(parentId) ? 'ov-edge on-path' : 'ov-edge',
					type: 'default',
					animated: false
				});
			}
		});

		await edges.set([...edgeList]);
		await nodes.set([...nodeList]);
	};

	const setLayoutDirection = (direction: LayoutDirection) => {
		layoutDirection = direction;
		drawFlow(layoutDirection);
	};

	onMount(() => {
		drawFlow(layoutDirection);

		const stopNodesInitialized = nodesInitialized.subscribe(async (initialized) => {
			// Refit only when the conversation itself changed - a new message, or
			// another branch opened. Opening or closing an agent lane re-measures
			// cards too, and refitting then snapped the view off the lane it had
			// just framed.
			const key = `${Object.keys(history.messages).join(',')}|${history.currentId}`;
			if (initialized && !pinned && key !== fittedFor) {
				fittedFor = key;
				await tick();
				await refit();
			}
		});
		const stopWidth = width.subscribe((value) => {
			if (value && !pinned) refit();
		});
		const stopHeight = height.subscribe((value) => {
			if (value && !pinned) refit();
		});

		return () => {
			console.log('Overview destroyed');
			stopNodesInitialized();
			stopWidth();
			stopHeight();
			nodes.set([]);
			edges.set([]);
		};
	});
</script>

<div class="w-full h-full relative">
	{#if $nodes.length > 0}
		<Flow
			{nodes}
			{nodeTypes}
			{edges}
			{setLayoutDirection}
			bind:pinned
			on:nodeclick={(e) => {
				onNodeClick(e.detail);
				const clickedMessageId = e.detail.node.data.message.id as string;
				selectedMessageId = clickedMessageId;
				if (!pinned) {
					fitView({ nodes: [{ id: clickedMessageId }], ...GLIDE });
				}
			}}
		/>
	{/if}
</div>
