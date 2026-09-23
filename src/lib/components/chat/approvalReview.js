/*
 * The sign-off panel's reading aids, applied to the draft once it is drawn:
 * - every [n] becomes a chip that opens the passage it rests on;
 * - each check is matched to the lines it speaks about, so hovering it can
 *   light them up;
 * - on a second try, the lines rewritten since the first are found, so they
 *   can be shown beside what they replaced.
 * All matching is by shared words, the way the orchestrator matches an
 * objection to the change that answers it (`_revision`). A check or change
 * that matches no line clearly is left unmatched rather than pinned to the
 * wrong one.
 */
import { chipTitle, CHIP } from './Messages/Markdown/evidence';

const CITATION = /\s*\[(\d+(?:\s*,\s*\d+)*)\]/g;
const STOP = new Set(
	(
		'that this with from have been were will would should could there their them they then than ' +
		'when what which while where into onto only also each every more most less very much such ' +
		'same does done over about after before because within without must need needs used uses ' +
		'using answer result claim claims states stated says said source sources document draft ' +
		'line lines request given gives stay stays being into your you the and for are not'
	).split(' ')
);

const tokens = (text) =>
	new Set(
		(text.toLowerCase().match(/\d+(?:[.,]\d+)?|[a-z][a-z'-]{3,}/g) ?? []).filter((w) => !STOP.has(w))
	);

const plain = (text) =>
	text
		.replace(CITATION, ' ')
		.replace(/[*_`#>~]/g, '')
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, ' ')
		.trim();

/* The draft's leaf blocks: paragraphs, list items, headings, cells. A list
   item that holds its own paragraph counts once, as the paragraph. */
export function blocksOf(root) {
	const all = [...root.querySelectorAll('p, li, h1, h2, h3, h4, h5, h6, td, th')];
	return all.filter((el) => !all.some((other) => other !== el && el.contains(other)));
}

const textOf = (el) => {
	const copy = el.cloneNode(true);
	copy.querySelectorAll('.rv-cite, .rv-old, .rv-passage').forEach((n) => n.remove());
	return copy.textContent ?? '';
};

/* [n] -> a chip per cited document. Returns the chips made. */
export function chipCitations(root, sources, onChip) {
	const byN = new Map((sources ?? []).map((s) => [s.n, s]));
	const names = (sources ?? []).map((s) => s.name);
	const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
		acceptNode: (node) =>
			node.parentElement?.closest('pre, code, a, .rv-cite') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT
	});
	const hits = [];
	while (walker.nextNode()) {
		if (CITATION.test(walker.currentNode.nodeValue)) hits.push(walker.currentNode);
		CITATION.lastIndex = 0;
	}
	for (const node of hits) {
		const text = node.nodeValue;
		const frag = document.createDocumentFragment();
		let last = 0;
		for (const match of text.matchAll(CITATION)) {
			const ns = match[1].split(/\s*,\s*/).map(Number);
			if (!ns.every((n) => byN.has(n))) continue;
			frag.append(text.slice(last, match.index));
			for (const n of ns) {
				const source = byN.get(n);
				const chip = document.createElement('button');
				chip.type = 'button';
				chip.className = `rv-cite ${CHIP} ml-1`;
				chip.dataset.n = String(n);
				chip.title = source.name;
				chip.innerHTML =
					'<svg class="size-[0.7rem] shrink-0 opacity-75" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M4 1.75h5.25L12.5 5v9.25H4z"/><path d="M9 1.75V5h3.5"/></svg>';
				const label = document.createElement('span');
				label.className = 'truncate';
				label.textContent = chipTitle(source.name, names);
				chip.append(label);
				chip.addEventListener('click', () => onChip(chip, source));
				frag.append(chip);
			}
			last = match.index + match[0].length;
		}
		if (last === 0) continue;
		frag.append(text.slice(last));
		node.replaceWith(frag);
	}
	return [...root.querySelectorAll('.rv-cite')];
}

/* Which blocks each check speaks about: the blocks sharing its rarer words
   and figures, at most two, and only when at least two of them are shared. */
export function matchChecks(root, checks) {
	const blocks = blocksOf(root);
	const words = blocks.map((b) => tokens(textOf(b)));
	const spread = new Map();
	for (const set of words) for (const w of set) spread.set(w, (spread.get(w) ?? 0) + 1);
	return (checks ?? []).map((check) => {
		const wanted = tokens(check.text);
		const scored = blocks
			.map((block, i) => {
				const shared = [...wanted].filter((w) => words[i].has(w));
				return { block, shared: shared.length, score: shared.reduce((sum, w) => sum + 1 / spread.get(w), 0) };
			})
			.filter((s) => s.shared >= 2)
			.sort((a, b) => b.score - a.score);
		const best = scored[0]?.score ?? 0;
		return scored.filter((s) => s.score >= best * 0.7).slice(0, 2).map((s) => s.block);
	});
}

/* The blocks a second try rewrote or added, each with the line it replaced
   (empty for an addition). Changes found in no block are returned apart. */
export function findChanges(root, revision) {
	const blocks = blocksOf(root).map((el) => ({ el, text: plain(textOf(el)) }));
	const placed = [];
	const unplaced = [];
	for (const change of revision?.changes ?? []) {
		if (!change.added) {
			if (change.removed) unplaced.push(change);
			continue;
		}
		const probe = plain(change.added.replace(/…$/, '')).split(' ').slice(0, 9).join(' ');
		const hit = probe && blocks.find((b) => b.text.includes(probe));
		// The line it replaced, without its [n]: struck through, a citation
		// token reads as noise.
		if (hit) placed.push({ el: hit.el, removed: (change.removed ?? '').replace(CITATION, '').trim() });
		else unplaced.push(change);
	}
	return { placed, unplaced };
}
