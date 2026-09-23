/*
 * Trust view: each sentence of a 4CE answer, underlined by what it rests on.
 *
 * - backed: the sentence cites a source (it carries an evidence chip) - a
 *   fine solid underline;
 * - a figure 4CE checked: inside a backed sentence, a figure the no-model
 *   figure check found in the cited document - a green underline;
 * - could not be checked: a sentence one of ULTRON's could-not-check (or
 *   problem) lines speaks about - an amber dotted underline.
 * A sentence nothing speaks about is left plain, never guessed at. Hovering
 * a marked sentence shows what it rests on: the passage behind it, with the
 * shared figures picked out, or ULTRON's reason.
 *
 * Drawn with the CSS Custom Highlight API: ranges over the rendered text, no
 * change to the DOM the markdown renderer owns. Everything comes from the
 * answer itself - its ```4ce-receipt block (checks, sources, what was cited)
 * and the passages retrieved for it (`message.sources`).
 */
import { chipTitle, usableChecks } from './Markdown/evidence';

const NAMES = { src: 'trust-src', un: 'trust-un', fig: 'trust-fig', hover: 'trust-hover' };
const supported = () => typeof CSS !== 'undefined' && 'highlights' in CSS && typeof Highlight !== 'undefined';

function highlight(name, priority = 0) {
	let h = CSS.highlights.get(name);
	if (!h) {
		h = new Highlight();
		h.priority = priority;
		CSS.highlights.set(name, h);
	}
	return h;
}

const STOP = new Set(
	(
		'that this with from have been were will would should could there their them they then than ' +
		'when what which while where into only also each every more most less very much such same does ' +
		'done over about after before because within without must need needs used using answer result ' +
		'claim claims states stated says said source sources document draft line request given your you ' +
		'the and for are not supplied nothing confirms confirm check checked'
	).split(' ')
);
const tokens = (text) =>
	new Set(
		(String(text).toLowerCase().match(/\d+(?:[.,]\d+)?|[a-z][a-z'-]{3,}/g) ?? []).filter((w) => !STOP.has(w))
	);
const FIGURE = /(?<![\w.\-])\d+(?:[.,]\d+)?(?![\w])/g;
const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

export function receiptOf(content) {
	const m = String(content ?? '').match(/```4ce-receipt\s*\n([\s\S]*?)\n```/);
	if (!m) return null;
	try {
		return JSON.parse(m[1]);
	} catch {
		return null;
	}
}

/* The answer's own sentences: leaf paragraphs and list items above the rule
   that sets off the receipt, outside code, tables and folded sections. */
function blocksOf(root) {
	const hr = root.querySelector(':scope hr, hr');
	const all = [...root.querySelectorAll('p, li')].filter(
		(el) =>
			!el.closest('details, pre, code, table, blockquote, .receipt-strip, [data-no-trust]') &&
			(!hr || hr.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_PRECEDING)
	);
	return all.filter((el) => !all.some((other) => other !== el && el.contains(other)));
}

/* A block's text as one string, with where each text node sits in it and
   where each evidence chip falls. */
function readBlock(block) {
	const segments = [];
	const chips = [];
	let text = '';
	const walk = (node) => {
		for (const child of node.childNodes) {
			if (child.nodeType === Node.TEXT_NODE) {
				segments.push({ node: child, start: text.length, end: text.length + child.nodeValue.length });
				text += child.nodeValue;
			} else if (child.nodeType === Node.ELEMENT_NODE) {
				if (child.classList?.contains('evidence-chip')) {
					chips.push({ at: text.length, title: child.getAttribute('title') ?? '' });
				} else if (!/^(CODE|KBD|SVG|BUTTON)$/i.test(child.tagName)) {
					walk(child);
				}
			}
		}
	};
	walk(block);
	return { text, segments, chips };
}

function pointAt(segments, offset) {
	for (const s of segments) {
		if (offset >= s.start && offset <= s.end) return [s.node, offset - s.start];
	}
	const last = segments[segments.length - 1];
	return last ? [last.node, last.node.nodeValue.length] : null;
}

function rangeOf(segments, start, end) {
	const a = pointAt(segments, start);
	const b = pointAt(segments, end);
	if (!a || !b) return null;
	const r = new Range();
	try {
		r.setStart(a[0], a[1]);
		r.setEnd(b[0], b[1]);
	} catch {
		return null;
	}
	return r;
}

/* Sentence spans within a block's text, trimmed of surrounding space. */
function sentencesOf(text) {
	const spans = [];
	let start = 0;
	const re = /[.!?](?=\s|$)/g;
	let m;
	while ((m = re.exec(text))) {
		spans.push([start, m.index + 1]);
		start = m.index + 1;
	}
	if (text.slice(start).trim()) spans.push([start, text.length]);
	return spans
		.map(([s, e]) => {
			while (s < e && /\s/.test(text[s])) s++;
			while (e > s && /\s/.test(text[e - 1])) e--;
			return [s, e];
		})
		.filter(([s, e]) => e - s > 2);
}

/* The clause of a retrieved passage a sentence rests on: the one sharing
   most of its figures and rarer words. */
function passageFor(sentence, source) {
	const docs = source?.document ?? [];
	if (!docs.length) return '';
	const want = tokens(sentence);
	let best = '';
	let score = -1;
	for (const doc of docs) {
		const clauses = String(doc)
			.split(/\n+|(?<=[.;])\s+(?=\d+(?:\.\d+)*\s)/)
			.map((c) => c.trim())
			.filter(Boolean);
		for (let i = 0; i < clauses.length; i++) {
			const clause = clauses[i];
			const have = tokens(clause);
			let s = 0;
			for (const w of want) if (have.has(w)) s += /\d/.test(w) ? 2 : 1;
			if (s > score) {
				score = s;
				best = clause.length < 90 && clauses[i + 1] ? `${clause} ${clauses[i + 1]}` : clause;
			}
		}
	}
	return best.length > 320 ? `${best.slice(0, best.lastIndexOf(' ', 320))}…` : best;
}

const matchOf = (source) => {
	const d = (source?.distances ?? []).filter((x) => typeof x === 'number');
	return d.length && d.every((x) => x >= 0 && x <= 1) ? Math.round(Math.max(...d) * 100) : null;
};

export function trustView(node, params) {
	if (!supported()) return {};
	let p = params;
	let marks = []; // { range, kind, info }
	let owned = { src: [], un: [], fig: [] };
	let hovered = null;
	let pop = null;
	let hideTimer = 0;
	let frame = 0;
	let observer = null;
	let debounce = 0;

	const clear = () => {
		for (const kind of Object.keys(owned)) {
			const h = CSS.highlights.get(NAMES[kind]);
			for (const r of owned[kind]) h?.delete(r);
		}
		owned = { src: [], un: [], fig: [] };
		marks = [];
		setHover(null);
	};

	const add = (kind, range) => {
		highlight(NAMES[kind], kind === 'fig' ? 2 : kind === 'un' ? 1 : 0).add(range);
		owned[kind].push(range);
	};

	function compute() {
		clear();
		if (!p?.enabled || !p?.done) return;
		const receipt = receiptOf(p.content);
		if (!receipt) return;
		const root = node.querySelector('.markdown-prose') ?? node;
		const names = receipt.sources ?? [];
		const sourceByName = new Map((p.sources ?? []).map((s) => [s?.source?.name, s]));
		const checks = usableChecks(receipt.checks);
		const figOk = new Set(
			checks
				.filter((c) => c.by === '4CE' && c.kind === 'ok')
				.flatMap((c) => (String(c.text).match(/\(([^)]*)\)/)?.[1] ?? '').split(/\s*,\s*/))
				.map((f) => f.replace(/…$/, '').trim())
				.filter(Boolean)
		);
		const figBad = checks
			.filter((c) => c.by === '4CE' && c.kind === 'problem')
			.map((c) => ({ figure: String(c.text).split(' ')[0], text: c.text }));
		const doubts = checks.filter((c) => c.by !== '4CE' && c.kind !== 'ok');

		const sentences = [];
		for (const block of blocksOf(root)) {
			const { text, segments, chips } = readBlock(block);
			const spans = sentencesOf(text);
			spans.forEach(([s, e], i) => {
				const next = spans[i + 1]?.[0] ?? text.length + 1;
				// A chip belongs to the sentence it sits in, or to the one it
				// directly follows ("… per minute. [1]").
				const cites = chips.filter((c) => (c.at >= s && c.at <= e) || (c.at > e && c.at < next && !text.slice(e, c.at).trim()));
				sentences.push({ block, text: text.slice(s, e), s, e, segments, cites, doubts: [] });
			});
		}

		// Each doubt goes to the sentence sharing most of its rarer words, and
		// only when at least two are shared.
		const words = sentences.map((x) => tokens(x.text));
		const spread = new Map();
		for (const set of words) for (const w of set) spread.set(w, (spread.get(w) ?? 0) + 1);
		for (const doubt of doubts) {
			const want = tokens(doubt.text);
			let best = null;
			let score = 0;
			sentences.forEach((x, i) => {
				const shared = [...want].filter((w) => words[i].has(w));
				const sc = shared.reduce((sum, w) => sum + 1 / spread.get(w), 0);
				if (shared.length >= 2 && sc > score) {
					best = x;
					score = sc;
				}
			});
			best?.doubts.push(doubt);
		}

		for (const x of sentences) {
			const range = rangeOf(x.segments, x.s, x.e);
			if (!range) continue;
			if (x.cites.length) {
				const title = x.cites[0].title;
				const source = sourceByName.get(title);
				add('src', range);
				const figures = [];
				for (const m of x.text.matchAll(FIGURE)) {
					if (figOk.has(m[0])) {
						const r = rangeOf(x.segments, x.s + m.index, x.s + m.index + m[0].length);
						if (r) add('fig', r);
						figures.push(m[0]);
					}
				}
				const bad = figBad.filter((b) => new RegExp(`(?<![\\w.])${b.figure.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![\\w])`).test(x.text));
				marks.push({
					range,
					kind: bad.length ? 'bad' : 'src',
					title,
					label: chipTitle(title, names),
					figures: [...new Set(figures)],
					passage: passageFor(x.text, source),
					match: matchOf(source),
					doubts: [...x.doubts, ...bad.map((b) => ({ kind: 'problem', text: b.text, by: '4CE' }))]
				});
			} else if (x.doubts.length) {
				add('un', range);
				marks.push({ range, kind: 'un', doubts: x.doubts });
			}
		}
	}

	/* ---- Hover ---- */
	function setHover(mark) {
		const h = supported() ? highlight(NAMES.hover, 3) : null;
		if (hovered) h?.delete(hovered.range);
		hovered = mark;
		if (mark) h?.add(mark.range);
	}

	function card(mark) {
		const passageHtml = (() => {
			if (!mark.passage) return '';
			let html = esc(mark.passage);
			for (const f of mark.figures ?? []) {
				html = html.replace(
					new RegExp(`(?<![\\w.])${f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![\\w])`, 'g'),
					(m) => `<mark>${m}</mark>`
				);
			}
			return `<p class="trust-pop-text">${html}</p>`;
		})();
		const doubts = (mark.doubts ?? [])
			.map(
				(d) =>
					`<p class="trust-pop-doubt"><span class="trust-tag ${d.kind === 'problem' ? 'bad' : 'un'}">${
						d.kind === 'problem' ? 'Problem' : "Couldn't be checked"
					}</span>${esc(d.text)} <span class="trust-by">${d.by === '4CE' ? '4CE' : 'ULTRON'}</span></p>`
			)
			.join('');
		if (mark.kind === 'un') {
			return `<div class="trust-pop-head"><span class="trust-tag un">Couldn't be checked</span><b>ULTRON</b></div>${(mark.doubts ?? [])
				.map((d) => `<p class="trust-pop-text">${esc(d.text)}</p>`)
				.join('')}`;
		}
		const figs = mark.figures?.length
			? `<span class="trust-muted">· ${mark.figures.length === 1 ? 'figure' : 'figures'} ${esc(mark.figures.join(', '))} checked by 4CE</span>`
			: '';
		return `<div class="trust-pop-head"><span class="trust-tag ok">Backed</span><b>${esc(mark.label)}</b>${
			mark.match != null ? `<span class="trust-muted">· ${mark.match}% match</span>` : ''
		}${figs}</div>${passageHtml}${doubts}`;
	}

	function place(mark) {
		if (!pop) {
			pop = document.createElement('div');
			pop.className = 'trust-pop';
			pop.setAttribute('role', 'tooltip');
			document.body.append(pop);
		}
		pop.innerHTML = card(mark);
		const rects = [...mark.range.getClientRects()];
		const last = rects[rects.length - 1] ?? mark.range.getBoundingClientRect();
		const first = rects[0] ?? last;
		const width = Math.min(416, window.innerWidth - 24);
		pop.style.width = `${width}px`;
		let left = Math.min(Math.max(12, first.left), window.innerWidth - width - 12);
		let top = last.bottom + 10;
		pop.style.left = `${left}px`;
		pop.style.top = `${top}px`;
		// Above the sentence when there is no room below it.
		const h = pop.offsetHeight;
		if (top + h > window.innerHeight - 12) pop.style.top = `${Math.max(12, first.top - h - 10)}px`;
		pop.classList.remove('on');
		void pop.offsetWidth;
		pop.classList.add('on');
	}

	function hide() {
		setHover(null);
		pop?.classList.remove('on');
	}

	const caretAt = (x, y) => {
		if (document.caretPositionFromPoint) {
			const c = document.caretPositionFromPoint(x, y);
			return c ? [c.offsetNode, c.offset] : null;
		}
		const r = document.caretRangeFromPoint?.(x, y);
		return r ? [r.startContainer, r.startOffset] : null;
	};

	function onMove(e) {
		if (!marks.length) return;
		const { clientX: x, clientY: y } = e;
		cancelAnimationFrame(frame);
		frame = requestAnimationFrame(() => {
			const at = caretAt(x, y);
			const mark =
				at &&
				marks.find(
					(m) =>
						m.range.isPointInRange(at[0], at[1]) &&
						[...m.range.getClientRects()].some((r) => x >= r.left - 2 && x <= r.right + 2 && y >= r.top - 2 && y <= r.bottom + 2)
				);
			if (mark) {
				clearTimeout(hideTimer);
				if (mark !== hovered) {
					setHover(mark);
					place(mark);
				}
			} else if (hovered) {
				clearTimeout(hideTimer);
				hideTimer = setTimeout(hide, 160);
			}
		});
	}
	const onLeave = () => {
		clearTimeout(hideTimer);
		hideTimer = setTimeout(hide, 160);
	};
	const onScroll = () => hovered && hide();

	node.addEventListener('mousemove', onMove);
	node.addEventListener('mouseleave', onLeave);
	window.addEventListener('scroll', onScroll, true);

	// The markdown renders after the message does, and a finished answer can
	// still redraw (a theme change, an edit): read it again once it settles.
	const schedule = () => {
		clearTimeout(debounce);
		debounce = setTimeout(compute, 300);
	};
	observer = new MutationObserver((records) => {
		if (records.some((r) => !(r.target instanceof Element && r.target.closest?.('.trust-pop')))) schedule();
	});
	observer.observe(node, { childList: true, subtree: true, characterData: true });
	schedule();

	return {
		update(next) {
			const changed =
				next?.enabled !== p?.enabled || next?.done !== p?.done || next?.content !== p?.content || next?.sources !== p?.sources;
			p = next;
			if (changed) schedule();
		},
		destroy() {
			clearTimeout(debounce);
			clearTimeout(hideTimer);
			cancelAnimationFrame(frame);
			observer?.disconnect();
			node.removeEventListener('mousemove', onMove);
			node.removeEventListener('mouseleave', onLeave);
			window.removeEventListener('scroll', onScroll, true);
			clear();
			pop?.remove();
		}
	};
}
