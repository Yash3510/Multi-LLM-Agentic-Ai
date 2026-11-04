// A fake data source for building the screens before the 4CE API exists: a few stored chats and
// a scripted answer replayed with realistic pacing. Nothing leaves the browser. The content is
// sector-neutral (rules R2 to R6, ids like CASE-0142).
import type { Chat, ChatSummary, DataSource, StreamEvent } from './types';

const hoursAgo = (hours: number) => new Date(Date.now() - hours * 3_600_000);

const ANSWER =
  'Yes. **R2 · Ratio** for CASE-0142 is 82.5 %, within the 85 % limit [1].\n\n' +
  '| Batch | Ratio | Limit |\n| --- | ---: | ---: |\n| Second | 82.5 % | 85 % |\n\n' +
  '- The reading comes from the second batch report [2].\n' +
  '- The first batch has no ratio recorded, so it was not assessed.';

/** An event before it is stamped with its arrival time. */
type Unstamped = {
  [K in StreamEvent['type']]: Omit<Extract<StreamEvent, { type: K }>, 'at'>;
}[StreamEvent['type']];

type Step = { after: number; event: Unstamped };

/** The run, step by step: each waits `after` ms (scaled by the pace) before its event. */
function script(): Step[] {
  const words = ANSWER.match(/\S+\s*/g) ?? [];
  return [
    {
      after: 400,
      event: {
        type: 'status',
        stage: 'planner',
        description: 'Planner: reading the request and choosing the crew',
      },
    },
    {
      after: 1200,
      event: {
        type: 'status',
        stage: 'reader',
        description: 'Reader: searching the knowledge base',
      },
    },
    {
      after: 300,
      event: {
        type: 'tool',
        call: { id: 't1', name: 'knowledge_search', input: 'R2 ratio CASE-0142', state: 'running' },
      },
    },
    {
      after: 900,
      event: {
        type: 'tool',
        call: {
          id: 't1',
          name: 'knowledge_search',
          input: 'R2 ratio CASE-0142',
          output: '2 passages',
          state: 'done',
        },
      },
    },
    {
      after: 100,
      event: {
        type: 'source',
        source: { index: 1, title: 'Rule R2 · Ratio', passage: 'The ratio shall not exceed 85 %.' },
      },
    },
    {
      after: 100,
      event: {
        type: 'source',
        source: {
          index: 2,
          title: 'CASE-0142 second batch report',
          passage: 'Measured ratio: 82.5 %.',
        },
      },
    },
    {
      after: 600,
      event: {
        type: 'status',
        stage: 'analyst',
        description: 'Analyst: comparing the reading with the limit',
      },
    },
    {
      after: 2600,
      event: { type: 'status', stage: 'author', description: 'Author: drafting the answer' },
    },
    ...words.map((text, index) => ({
      after: index === 0 ? 400 : 45,
      event: { type: 'delta' as const, text },
    })),
    {
      after: 500,
      event: {
        type: 'status',
        stage: 'challenger',
        description: 'Challenger: checking every figure against its source',
      },
    },
    {
      after: 2400,
      event: {
        type: 'status',
        stage: 'challenger',
        description: 'Challenger: pass, every figure is supported',
      },
    },
    {
      after: 300,
      event: { type: 'status', stage: 'sign-off', description: 'Waiting for sign-off' },
    },
    {
      after: 200,
      event: {
        type: 'sign-off',
        request: {
          checks: [
            { label: 'R2 · Ratio within its limit', verdict: 'pass' },
            { label: 'Every figure has a source', verdict: 'pass' },
          ],
        },
      },
    },
  ];
}

function failing(): Step[] {
  return [
    ...script().slice(0, 7),
    { after: 800, event: { type: 'error', message: 'All connection attempts failed' } },
  ];
}

function closing(outcome: 'released' | 'withheld', by: string): Step[] {
  return [
    { after: 300, event: { type: 'decision', outcome, by } },
    {
      after: 200,
      event: {
        type: 'receipt',
        receipt: {
          fingerprint: '3f9a21c0b7e4d815',
          model: 'qwen/qwen3-8b',
          seconds: 9.4,
          sources: 2,
          signedBy: by,
          externalCalls: 0,
          folds: [
            {
              title: 'Full provenance',
              body: '| Figure | Source |\n| --- | --- |\n| 82.5 % | [2] |\n| 85 % limit | [1] |',
            },
            {
              title: 'Analyst — analysis · qwen/qwen3-8b',
              body: 'The second batch report gives a ratio of 82.5 % [2]; rule R2 sets the limit at 85 % [1]. The first batch has no ratio, so it is not assessed.',
            },
            {
              title: 'Challenger — verification — PASS · qwen/qwen3-1.7b',
              body: 'Every figure in the answer appears in the source it cites.',
            },
          ],
        },
      },
    },
    { after: 100, event: { type: 'done' } },
  ];
}

/** A finished, released run stored with a chat, as a reloaded chat would come back. */
function storedRun(id: string, question: string, at: Date) {
  let time = at.getTime();
  const events: StreamEvent[] = [...script(), ...closing('released', 'Asha Rao')].map((step) => {
    time += step.after;
    return { ...step.event, at: time };
  });
  const text = events.flatMap((event) => (event.type === 'delta' ? [event.text] : [])).join('');
  return [
    { id: `${id}-q`, role: 'user' as const, text: question, at },
    { id: `${id}-a`, role: 'response' as const, text, at, events, finished: true },
  ];
}

const CHATS: Chat[] = [
  {
    id: 'c-0142',
    title: 'Is R2 · Ratio within the limit for CASE-0142?',
    updated: hoursAgo(2),
    outcome: 'released',
    messages: storedRun('m-0142', 'Is R2 · Ratio within the limit for CASE-0142?', hoursAgo(2)),
  },
  {
    id: 'c-0143',
    title: 'Review the duration readings for CASE-0143',
    updated: hoursAgo(30),
    outcome: 'released',
    messages: [],
  },
  {
    id: 'c-0139',
    title: 'Cost of the second batch against R4',
    updated: hoursAgo(4 * 24),
    outcome: 'released',
    messages: [],
  },
  {
    id: 'c-0131',
    title: 'Draft an approval note for CASE-0131',
    updated: hoursAgo(12 * 24),
    outcome: 'released',
    messages: [],
  },
  {
    id: 'c-hi',
    title: 'hi',
    updated: hoursAgo(21 * 24),
    outcome: 'direct',
    messages: [
      { id: 'm-hi-1', role: 'user', text: 'hi', at: hoursAgo(21 * 24) },
      {
        id: 'm-hi-2',
        role: 'response',
        text: 'Hello. What can I help you with?',
        at: hoursAgo(21 * 24),
        finished: true,
        direct: { status: 'Answered directly', model: 'qwen/qwen3-1.7b', seconds: 7.9 },
      },
    ],
  },
  {
    id: 'c-0120',
    title: 'Audit this deployment for sovereignty',
    updated: hoursAgo(40 * 24),
    outcome: 'released',
    messages: [],
  },
];

const sleep = (ms: number, signal?: AbortSignal) =>
  new Promise<void>((resolve) => {
    if (!ms || signal?.aborted) return resolve();
    const timer = setTimeout(resolve, ms);
    signal?.addEventListener('abort', () => (clearTimeout(timer), resolve()), { once: true });
  });

async function* replay(steps: Step[], pace: number, signal?: AbortSignal) {
  let at = Date.now();
  for (const step of steps) {
    await sleep(step.after * pace, signal);
    if (signal?.aborted) return;
    at += step.after;
    const event: StreamEvent = { ...step.event, at };
    yield event;
  }
}

/** `pace` scales every wait: 1 is real time, 0 replays at once (tests). */
export function createFakeSource({ pace = 1 }: { pace?: number } = {}): DataSource {
  return {
    async listChats(): Promise<ChatSummary[]> {
      return [...CHATS]
        .sort((a, b) => b.updated.getTime() - a.updated.getTime())
        .map(({ id, title, updated, outcome }) => ({ id, title, updated, outcome }));
    },
    async getChat(id) {
      return CHATS.find((chat) => chat.id === id);
    },
    ask(_chatId, question, signal) {
      // A question about the server being down replays a run that stops at the Analyst, so the
      // run error card can be seen without a backend.
      if (/server down/i.test(question)) return replay(failing(), pace, signal);
      return replay(script(), pace, signal);
    },
    decide(_chatId, outcome, by, signal) {
      return replay(closing(outcome, by), pace, signal);
    },
  };
}
