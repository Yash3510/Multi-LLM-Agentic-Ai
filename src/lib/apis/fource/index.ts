import { WEBUI_API_BASE_URL } from '$lib/constants';

// 4CE: the sovereignty page's API (backend/open_webui/routers/fource.py).

const call = async (token: string, path: string, method: 'GET' | 'POST' = 'GET') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/fource${path}`, {
		method,
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err?.detail ?? err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export type EgressEvent = {
	first: number;
	last: number;
	process: string;
	pid: number;
	role: string;
	remote: string;
	direction: 'in' | 'out';
	state: string;
	flows: number;
};

export type Canary = {
	at: number;
	target: string;
	outcome: 'blocked' | 'reachable';
	detail: string;
	ms: number;
};

export type Egress = {
	running: boolean;
	generation: number;
	since: number;
	now: number;
	samples: number;
	interval_ms: number;
	last_sample: number;
	error: string;
	mode: string;
	flows: Record<'local' | 'lan_in' | 'lan_expected' | 'lan_out' | 'external' | 'canary', number>;
	external: EgressEvent[];
	lan_out: EgressEvent[];
	scope: { pid: number; process: string; role: string; listening: number[] }[];
	// A browser one of them opened: the person's browsing, not watched.
	excluded?: { pid: number; process: string; role: string }[];
	live: {
		process: string;
		pid: number;
		role: string;
		local: string;
		remote: string;
		state: string;
		kind: string;
		direction: 'in' | 'out';
	}[];
	canaries: Canary[];
	canary_target: string;
	expected_lan: string[];
	limits: string[];
};

export type Audit = {
	checks: { label: string; ok: boolean; detail: string }[];
	passed: number;
	total: number;
};

export const getEgress = (token: string): Promise<Egress> => call(token, '/egress');
export const runCanary = (token: string): Promise<Canary> => call(token, '/egress/canary', 'POST');
export const resetEgress = (token: string): Promise<Egress> => call(token, '/egress/reset', 'POST');
export const getAudit = (token: string): Promise<Audit> => call(token, '/audit');

// 4CE's audit trail (backend/open_webui/utils/fource_audit.py): append-only,
// each entry sealed with the hash of the one before it.
export type TrailEntry = {
	seq: number;
	at: number;
	action: string;
	prev: string;
	hash: string;
	[field: string]: unknown;
};

export type Trail = {
	entries: TrailEntry[];
	path: string;
	count: number;
	head: string;
	last_error: string;
	failed_writes: number;
	verify?: { ok: boolean; entries: number; head: string; broken_at: number | null; reason: string };
};

export const getTrail = (token: string, after = 0, verify = false): Promise<Trail> =>
	call(token, `/audit-trail?after=${after}&limit=40${verify ? '&verify=true' : ''}`);

export type RegistryModel = {
	id: string;
	family?: string;
	modalities?: string[];
	capabilities?: string[];
	context?: number;
	size_gb?: number;
	licence?: string;
	served?: boolean;
};

export type Registry = {
	models: RegistryModel[];
	embedding: RegistryModel;
	routing: Record<string, string[]>;
	// The hardware profile installed: models.json or one of 4ce/profiles/.
	profile?: { name?: string; gpu?: string; measured?: boolean };
};

export const getModels = (token: string): Promise<Registry> => call(token, '/models');
