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
