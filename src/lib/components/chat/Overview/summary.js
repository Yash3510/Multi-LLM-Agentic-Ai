/*
 * What an Overview card says about a message, derived from the same status
 * stream as the stage rail in the chat - so the map and the answer can never
 * disagree about how a run went.
 */

const STAGE_OF = {
	tony: 'TONY',
	tony_plan: 'TONY',
	router: 'TONY',
	tony_replan: 'TONY',
	friday: 'FRIDAY',
	jarvis: 'JARVIS',
	ultron: 'ULTRON',
	approval: 'YOU'
};
const STAGES = ['TONY', 'FRIDAY', 'JARVIS', 'ULTRON', 'YOU'];

const LABELS = {
	direct: 'Direct reply',
	released: 'Released',
	withheld: 'Withheld',
	complete: 'Complete',
	reviewing: 'Your review',
	working: 'Working',
	stopped: 'Stopped',
	failed: 'Failed',
	interrupted: 'Interrupted'
};

/**
 * The run behind an assistant message: which stages it reached, which one is
 * live, and how it ended. `null` for messages that no 4CE run produced.
 */
export function runSummary(message) {
	const history = (message?.statusHistory ?? []).filter(Boolean);
	if (!history.length) return null;

	const reached = new Set();
	let direct = false;
	let outcome = null;
	let lastStage = null;

	for (const status of history) {
		const stage = STAGE_OF[status.action];
		if (stage) {
			reached.add(stage);
			lastStage = stage;
			if (stage === 'YOU' && status.done) outcome = 'withheld';
		} else if (status.action === 'chat') {
			direct = true;
		} else if (status.action === 'stopped') {
			outcome = 'stopped';
		} else if (status.action === 'error') {
			outcome = 'failed';
		} else if ((status.action === 'done' || status.action === 'tool') && !outcome) {
			outcome = reached.has('YOU') ? 'released' : 'complete';
		}
	}

	if (direct) outcome = outcome === 'failed' ? 'failed' : 'direct';

	const live = message?.done !== true;
	if (live && !outcome) outcome = lastStage === 'YOU' ? 'reviewing' : 'working';
	if (!live && !outcome) outcome = 'interrupted';

	return {
		chain: !direct && reached.size > 1,
		live: live && (outcome === 'working' || outcome === 'reviewing'),
		outcome,
		label: LABELS[outcome] ?? '',
		stages: STAGES.map((name) => ({
			name,
			reached: reached.has(name),
			active: live && name === lastStage
		}))
	};
}

/**
 * A readable preview of a message: its first lines of prose, without the
 * markdown marks, tables, rules and the provenance a 4CE answer carries.
 */
export function snippet(text) {
	const lines = String(text ?? '')
		.replace(/<details>[\s\S]*?<\/details>/g, '')
		.replace(/<[^>]+>/g, ' ')
		.split('\n')
		// A line wholly in italics is a footnote - 4CE's "Direct reply · model ·
		// 0.4s" note, say - which the card's chip already says better.
		.filter((line) => !/^\s*([*_])(?!\1).*[^*_]\1\s*$/.test(line))
		.map((line) =>
			line
				.replace(/^\s{0,3}(#{1,6}|>|[-*+]|\d+[.)])\s+/, '')
				.replace(/\*\*|__|`/g, '')
				.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
				.trim()
		)
		.filter((line) => line && !/^\|/.test(line) && !/^[-—–*_=\s]{3,}$/.test(line));
	return lines.slice(0, 2).join(' — ');
}

/** Initials for a person's card, first and last name: "Pranay Harish Munj" -> "PM". */
export function initials(name) {
	const words = String(name ?? '')
		.split(/\s+/)
		.map((w) => w.replace(/[^\p{L}\p{N}]/gu, ''))
		.filter(Boolean);
	const last = words.length > 1 ? words[words.length - 1][0] : '';
	return ((words[0]?.[0] ?? '') + last).toUpperCase() || '·';
}

const ROLES = {
	FRIDAY: 'Analysis',
	JARVIS: 'Deliverable',
	ULTRON: 'Verification',
	YOU: 'Approval'
};
const CLOSING = new Set(['done', 'stopped', 'error', 'tool', 'chat']);

function fmt(seconds) {
	if (seconds < 0.1) return '<0.1s';
	if (seconds < 60) return `${seconds.toFixed(1)}s`;
	const minutes = Math.floor(seconds / 60);
	return `${minutes}m ${String(Math.round(seconds % 60)).padStart(2, '0')}s`;
}

/**
 * The agents behind one 4CE answer, for the Overview's expanded lane: each
 * one's role, how long it took (from the server timestamps the orchestrator
 * sends), how many passes it made, the model it ran on when the run said so,
 * and - for ULTRON and the human gate - the verdict.
 */
export function agentDetails(message) {
	const history = (message?.statusHistory ?? []).filter(Boolean);
	const live = message?.done !== true;
	const agents = {};
	for (const name of Object.keys(ROLES)) {
		agents[name] = { name, role: ROLES[name], runs: 0, seconds: 0, timed: false, verdict: null, model: null };
	}

	let current = null;
	let started = null;
	const close = (ts) => {
		if (current && started != null && ts != null) {
			agents[current].seconds += ts - started;
			agents[current].timed = true;
		}
		current = null;
		started = null;
	};

	for (const status of history) {
		const stage = STAGE_OF[status.action];
		if (stage && stage !== 'TONY') {
			if (current !== stage) {
				close(status.ts);
				current = stage;
				started = status.ts ?? null;
				agents[stage].runs += 1;
			}
			const model = (status.facts ?? [])
				.map((fact) => String(fact).match(/^(?:Running|Checking) on (\S+?)(?:,|$)/)?.[1])
				.find(Boolean);
			if (model) agents[stage].model = model.split('/').pop();
			if (stage === 'ULTRON' && /PASS|FAIL/.test(status.description ?? '')) {
				agents.ULTRON.verdict = /FAIL/.test(status.description) ? 'FAIL' : 'PASS';
			}
			if (stage === 'YOU' && status.done) {
				agents.YOU.verdict = /no reviewer/i.test(status.description ?? '') ? 'not answered' : 'withheld';
				close(status.ts);
			}
		} else if (stage === 'TONY' || CLOSING.has(status.action)) {
			close(status.ts);
			if ((status.action === 'done' || status.action === 'tool') && agents.YOU.runs && !agents.YOU.verdict) {
				agents.YOU.verdict = 'released';
			}
			if (status.action === 'stopped' && agents.YOU.runs && !agents.YOU.verdict) agents.YOU.verdict = 'stopped';
		}
	}

	return Object.values(agents).map((agent) => {
		const active = live && agent.name === current;
		const tone =
			agent.name === 'YOU'
				? agent.verdict === 'released'
					? 'good'
					: agent.verdict
						? 'warn'
						: null
				: agent.name === 'ULTRON' && agent.verdict === 'FAIL'
					? 'warn'
					: agent.name === 'ULTRON' && agent.verdict === 'PASS'
						? 'good'
						: null;
		return {
			...agent,
			active,
			reached: agent.runs > 0,
			time: active ? null : agent.timed ? fmt(agent.seconds) : null,
			note:
				agent.name === 'YOU'
					? active
						? 'reviewing'
						: agent.verdict
					: active
						? 'working'
						: agent.verdict,
			tone
		};
	});
}

/**
 * The same run, but one entry per pass rather than one per agent: FRIDAY,
 * JARVIS, ULTRON, and again from FRIDAY whenever ULTRON sends the work back,
 * ending at the human gate. The Overview stacks these straight down, so a
 * reader sees the order things actually happened in, re-runs included.
 */
export function agentRuns(message) {
	const history = (message?.statusHistory ?? []).filter(Boolean);
	const live = message?.done !== true;
	const runs = [];
	const counts = {};
	let current = null; // the open run

	const close = (ts) => {
		if (current && current.start != null && ts != null) {
			current.seconds = Math.max(0, ts - current.start);
			current.timed = true;
		}
		current = null;
	};

	for (const status of history) {
		const stage = STAGE_OF[status.action];
		if (stage && stage !== 'TONY') {
			if (current?.name !== stage) {
				close(status.ts);
				counts[stage] = (counts[stage] ?? 0) + 1;
				current = {
					name: stage,
					role: ROLES[stage],
					pass: counts[stage],
					start: status.ts ?? null,
					seconds: 0,
					timed: false,
					model: null,
					verdict: null
				};
				runs.push(current);
			}
			const model = (status.facts ?? [])
				.map((fact) => String(fact).match(/^(?:Running|Checking) on (\S+?)(?:,|$)/)?.[1])
				.find(Boolean);
			if (model) current.model = model.split('/').pop();
			if (stage === 'ULTRON' && /PASS|FAIL/.test(status.description ?? '')) {
				current.verdict = /FAIL/.test(status.description) ? 'FAIL' : 'PASS';
			}
			if (stage === 'YOU' && status.done) {
				current.verdict = /no reviewer/i.test(status.description ?? '') ? 'not answered' : 'withheld';
				close(status.ts);
			}
		} else if (stage === 'TONY' || CLOSING.has(status.action)) {
			const gate = current?.name === 'YOU' ? current : runs.findLast?.((run) => run.name === 'YOU');
			close(status.ts);
			if ((status.action === 'done' || status.action === 'tool') && gate && !gate.verdict) {
				gate.verdict = 'released';
			}
			if (status.action === 'stopped' && gate && !gate.verdict) gate.verdict = 'stopped';
		}
	}

	const openRun = live ? current : null;
	return runs.map((run) => {
		const active = run === openRun;
		const tone =
			run.name === 'YOU'
				? run.verdict === 'released'
					? 'good'
					: run.verdict
						? 'warn'
						: null
				: run.verdict === 'FAIL'
					? 'warn'
					: run.verdict === 'PASS'
						? 'good'
						: null;
		return {
			name: run.name,
			role: run.role,
			pass: run.pass,
			model: run.model,
			verdict: run.verdict,
			active,
			reached: true,
			time: active ? null : run.timed ? fmt(run.seconds) : null,
			note: run.name === 'YOU' ? (active ? 'reviewing' : run.verdict) : active ? 'working' : run.verdict,
			tone
		};
	});
}
