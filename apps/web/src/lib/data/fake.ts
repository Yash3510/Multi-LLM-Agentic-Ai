// A fake data source for building the screens before the 4CE API exists: a few stored chats and
// a scripted answer replayed with realistic pacing. Nothing leaves the browser. The content is
// sector-neutral (rules R2 to R6, ids like CASE-0142).
import type {
  Receipt,
  Chat,
  ChatSummary,
  DataSource,
  KnowledgeBase,
  KnowledgeDocument,
  KnowledgeFolder,
  Prompt,
  PromptVersion,
  Skill,
  Tool,
  UserSettings,
  Automation,
  Calendar,
  CalendarEvent,
  Channel,
  ChannelMessage,
  Note,
  ServerFunction,
  Feedback,
  LeaderboardEntry,
  Group,
  StoredPermissions,
  AdminUser,
  LedgerEntry,
  Profile,
  Usage,
  UsageDay,
  Memory,
  StreamEvent,
  User,
  WorkspaceItem,
  WorkspaceModel,
} from './types';

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
            { label: 'R2 · Ratio within its limit', verdict: 'pass', cites: [1, 2] },
            { label: 'Every figure has a source', verdict: 'pass', cites: [2] },
          ],
        },
      },
    },
  ];
}

function replanned(): Step[] {
  const run = script();
  const author = run.findIndex(
    (step) => step.event.type === 'status' && step.event.stage === 'author',
  );
  const challenger = run.findIndex(
    (step) => step.event.type === 'status' && step.event.stage === 'challenger',
  );
  const deltas = run.slice(author + 1, challenger);
  const signOff = run.at(-1);
  const request = signOff?.event.type === 'sign-off' ? signOff.event.request : { checks: [] };
  return [
    ...run.slice(0, author + 1),
    {
      after: 2200,
      event: {
        type: 'status',
        stage: 'challenger',
        description: 'Challenger: fail, the ratio is rounded without saying so',
      },
    },
    {
      after: 600,
      event: {
        type: 'status',
        stage: 'replan',
        description: 'Replanned, with the objections attached for the Analyst and Author',
      },
    },
    {
      after: 500,
      event: {
        type: 'status',
        stage: 'analyst',
        description: 'Analyst: checking the exact reading',
      },
    },
    {
      after: 1800,
      event: { type: 'status', stage: 'author', description: 'Author: revising the answer' },
    },
    ...deltas,
    {
      after: 500,
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
          ...request,
          revision: {
            try: 2,
            objections: [{ by: 'Challenger', text: 'The ratio is rounded without saying so.' }],
            changes: [
              {
                removed: 'Yes. R2 · Ratio for CASE-0142 is about 83 %, within the limit [1].',
                added: 'Yes. R2 · Ratio for CASE-0142 is 82.5 %, within the 85 % limit [1].',
              },
            ],
          },
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

type Folds = NonNullable<Receipt['folds']>;

const FOLDS: Folds = [
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
];

/** Every agent's output and a second try, so the details panel has each tab full. */
const DEMO_FOLDS: Folds = [
  {
    title: 'Full provenance',
    body: '| Figure | Source |\n| --- | --- |\n| 82.5 % | [2] |\n| 85 % limit | [1] |\n| First batch: no ratio | [3] |',
  },
  {
    title: 'Planner — plan · qwen/qwen3-8b',
    body: 'Find rule R2 and its limit, read both batch reports for CASE-0142, compare, then have the answer checked.',
  },
  {
    title: 'Reader — retrieval · qwen/qwen3-8b',
    body: 'Three passages: the rule [1], the second batch report [2] and the first batch report [3].',
  },
  FOLDS[1]!,
  {
    title: 'Author — draft · qwen/qwen3-8b',
    body: 'First draft said "about 83 %". Second draft gives the exact reading, 82.5 %, and the limit it is compared with.',
  },
  {
    title: 'Challenger — verification, try 1 — FAIL · qwen/qwen3-1.7b',
    body: 'The ratio is rounded without saying so.',
  },
  {
    title: 'Challenger — verification, try 2 — PASS · qwen/qwen3-1.7b',
    body: 'Every figure in the answer appears in the source it cites.',
  },
];

/** The replanned run with a third source, which the answer does not cite. */
function demo(): Step[] {
  const run = replanned();
  const analyst = run.findIndex(
    (step) => step.event.type === 'status' && step.event.stage === 'analyst',
  );
  return [
    ...run.slice(0, analyst),
    {
      after: 100,
      event: {
        type: 'source',
        source: {
          index: 3,
          title: 'CASE-0142 first batch report',
          passage: 'Ratio: not measured.',
        },
      },
    },
    ...run.slice(analyst),
  ];
}

function closing(outcome: 'released' | 'withheld', by: string, folds = FOLDS, sources = 2): Step[] {
  return [
    { after: 300, event: { type: 'decision', outcome, by } },
    {
      after: 200,
      event: {
        type: 'receipt',
        receipt: {
          fingerprint: '0604685d984d94b44870bea051662d5c981671e220f8073eae5ab3c26543b5f7',
          model: 'qwen/qwen3-8b',
          seconds: 9.4,
          sources,
          signedBy: by,
          externalCalls: 0,
          folds,
        },
      },
    },
    { after: 100, event: { type: 'done' } },
  ];
}

/** A finished, released run stored with a chat, as a reloaded chat would come back. */
function storedRun(
  id: string,
  question: string,
  at: Date,
  run = script(),
  folds = FOLDS,
  sources = 2,
) {
  let time = at.getTime();
  const events: StreamEvent[] = [...run, ...closing('released', 'Asha Rao', folds, sources)].map(
    (step) => {
      time += step.after;
      return { ...step.event, at: time };
    },
  );
  const text = events.flatMap((event) => (event.type === 'delta' ? [event.text] : [])).join('');
  return [
    { id: `${id}-q`, role: 'user' as const, text: question, at },
    { id: `${id}-a`, role: 'response' as const, text, at, events, finished: true },
  ];
}

const CHATS: Chat[] = [
  {
    id: 'c-demo',
    title: 'Details demo: R2 · Ratio for CASE-0142, second try',
    updated: hoursAgo(1),
    outcome: 'released',
    messages: storedRun(
      'm-demo',
      'Is R2 · Ratio within the limit for CASE-0142? Check both batches.',
      hoursAgo(1),
      demo(),
      DEMO_FOLDS,
      3,
    ),
  },
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
// Stand-ins sized like the capture account's workspace on the running app (3 base models, 3
// knowledge bases, 7 tools), with neutral names.
const BASE_MODELS: WorkspaceItem[] = [
  { id: '4ce-tony', name: '4CE / TONY (Orchestrator)' },
  { id: 'qwen/qwen3-vl-4b', name: 'qwen/qwen3-vl-4b' },
  { id: 'qwen/qwen3-1.7b', name: 'qwen/qwen3-1.7b' },
];
// Two months old, as on the running app, so the rows read "2 months ago".
const knowledge = (): KnowledgeBase[] =>
  [0, 1, 2].map((index) => ({
    id: `plant-notes-${index + 1}`,
    name: 'Plant Notes',
    description: 'Standard operating procedures and reference readings for rotating equipment.',
    updated: new Date(Date.now() - 60 * 86_400_000),
    owner: { name: '4CE Administrator', email: 'admin@example.test' },
    writable: true,
    source: 'local',
  }));
// The capture account's seven tools, a month old, with neutral descriptions.
const tools = (): Tool[] =>
  [
    [
      'Sovereignty Check',
      'Audits live configuration for anything that could send data off-premise.',
    ],
    [
      'Threshold Check',
      'Assesses readings against set thresholds and cites the clause that decided each.',
    ],
    ['Engineering Calculations', 'Works rates, intervals and margins in code, every step shown.'],
    [
      'Workspace Files',
      'Reads and writes files in one workspace folder, keeping earlier versions; every access audited.',
    ],
    [
      'Spreadsheets',
      'Reads workbooks with their formulas and writes changes to a copy as live formulas; never the source.',
    ],
    ['Sovereign Sandbox', 'Runs Python in a disposable, network-disabled container.'],
    ['Deliverables', 'Produces formatted .docx deliverables from agent output.'],
  ].map(([name, description], index) => ({
    id: name.toLowerCase().replace(/ /g, '_'),
    name: `4CE ${name}`,
    description,
    version: '0.1.0',
    content: `"""\ntitle: 4CE ${name}\nversion: 0.1.0\n"""\n\nclass Tools:\n    pass\n`,
    updated: new Date(Date.now() - (35 + index) * 86_400_000),
    owner: { name: '4CE Administrator', email: 'admin@example.test' },
    writable: true,
  }));

type StoredDocument = KnowledgeDocument & { base: string; text: string };
type StoredFolder = KnowledgeFolder & { base: string };

// The first base's two documents, as on the running app (sizes 2.0 KB and 1.3 KB).
const documents = (): StoredDocument[] =>
  [
    ['MEC-014_readings_unit-101B.txt', 2048, 'Bearing temperature readings for unit 101B.'],
    ['MEC-014_notes.txt', 1331, 'Notes on the unit 101B readings.'],
  ].map(([name, size, text], index) => ({
    id: `doc-${index + 1}`,
    base: 'plant-notes-1',
    name: String(name),
    size: Number(size),
    text: String(text),
    updated: new Date(Date.now() - 60 * 86_400_000),
    owner: { name: '4CE Administrator', email: 'admin@example.test' },
  }));

/** A year and a half of usage ending today, with a few active days near the end: 12 messages
 * over 6 chats, all with the orchestrator, peaking at 27.3k tokens; the longest streak is 2. */
function usage(today = new Date()): Usage {
  const active: Record<number, [messages: number, chats: number, tokens: number]> = {
    40: [2, 1, 27_300],
    33: [4, 2, 8_000],
    26: [2, 1, 6_000],
    25: [2, 1, 5_000],
    19: [2, 1, 3_900],
  };
  const start = Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate());
  const daily: UsageDay[] = Array.from({ length: 548 }, (_, index) => {
    const ago = 547 - index;
    const [messages, chats, tokens] = active[ago] ?? [0, 0, 0];
    const models: Record<string, number> = messages ? { '4ce-tony': messages } : {};
    return {
      date: new Date(start - ago * 86_400_000).toISOString().slice(0, 10),
      messages,
      chats,
      tokens,
      models,
    };
  });
  const add = (a: UsageDay, b: UsageDay): UsageDay => ({
    date: a.date,
    messages: a.messages + b.messages,
    chats: a.chats + b.chats,
    tokens: a.tokens + b.tokens,
    models: Object.fromEntries(
      [...new Set([...Object.keys(a.models), ...Object.keys(b.models)])].map((id) => [
        id,
        (a.models[id] ?? 0) + (b.models[id] ?? 0),
      ]),
    ),
  });
  const weeks = new Map<string, UsageDay>();
  for (const day of daily) {
    const date = new Date(`${day.date}T00:00:00Z`);
    date.setUTCDate(date.getUTCDate() - ((date.getUTCDay() + 6) % 7));
    const monday = date.toISOString().slice(0, 10);
    const week = weeks.get(monday);
    weeks.set(monday, week ? add(week, day) : { ...day, date: monday });
  }
  const cumulative: UsageDay[] = [];
  for (const day of daily) {
    const before = cumulative.at(-1);
    cumulative.push(before ? { ...add(before, day), date: day.date } : day);
  }
  return {
    totals: {
      lifetimeTokens: 50_200,
      peakDailyTokens: 27_300,
      longestChatSeconds: 0,
      currentStreak: 0,
      longestStreak: 2,
      totalChats: 6,
      modelsUsed: 1,
      messages: 12,
      userMessages: 6,
      assistantMessages: 6,
    },
    daily,
    weekly: [...weeks.values()],
    cumulative,
    insights: {
      averageTokensPerChat: 8_367,
      averageMessagesPerActiveDay: 2.4,
      userMessageShare: 50,
      assistantMessageShare: 50,
    },
    topModels: [{ id: '4ce-tony', messages: 6, tokens: 50_200 }],
    topTools: [],
  };
}

/** Elo ratings from feedback, as a pairwise comparison per record (K 32, starting at 1000). */
function standings(feedback: Feedback[]): LeaderboardEntry[] {
  const board = new Map<string, LeaderboardEntry & { counts: Map<string, number> }>();
  const entry = (modelId: string) => {
    const found = board.get(modelId) ?? {
      modelId,
      rating: 1000,
      won: 0,
      lost: 0,
      tags: [],
      counts: new Map<string, number>(),
    };
    board.set(modelId, found);
    return found;
  };
  for (const one of [...feedback].sort((a, b) => a.created.getTime() - b.created.getTime())) {
    const model = entry(one.modelId);
    for (const tag of one.tags) model.counts.set(tag, (model.counts.get(tag) ?? 0) + 1);
    if (one.result === 0) continue;
    for (const other of one.siblings.map(entry)) {
      const [winner, loser] = one.result === 1 ? [model, other] : [other, model];
      const expected = 1 / (1 + 10 ** ((loser.rating - winner.rating) / 400));
      winner.rating += 32 * (1 - expected);
      loser.rating -= 32 * (1 - expected);
      winner.won += 1;
      loser.lost += 1;
    }
  }
  return [...board.values()].map(({ counts, ...rest }) => ({
    ...rest,
    rating: Math.round(rest.rating),
    tags: [...counts].map(([tag, count]) => ({ tag, count })).sort((a, b) => b.count - a.count),
  }));
}

export function createFakeSource({
  pace = 1,
  feedback: seeded = [],
}: { pace?: number; feedback?: Feedback[] } = {}): DataSource {
  const models: WorkspaceModel[] = [];
  const bases = knowledge();
  const docs = documents();
  const folders: StoredFolder[] = [];
  const prompts: Prompt[] = [];
  let settings: UserSettings = {};
  let memories: Memory[] = [];
  let profile: Omit<Profile, 'name'> = { avatar: { kind: 'default' }, variables: {} };
  // This source's own copy, so bulk changes stay with it.
  let chats: Chat[] = [...CHATS];
  const archived = new Set<string>();
  // Each change is a tick later than the last, so newest-first order holds within one millisecond.
  let clock = 0;
  const stamp = () => new Date((clock = Math.max(clock + 1, Date.now())));
  const skills: Skill[] = [];
  const toolList = tools();
  const tool = (id: string) => toolList.find((one) => one.id === id);
  const skill = (id: string) => skills.find((one) => one.id === id);
  const versions = new Map<string, PromptVersion[]>();
  const author = () => ({ name: user?.name ?? 'Deleted User' });
  const prompt = (id: string) => prompts.find((one) => one.id === id);
  const count = (base: string) => docs.filter((doc) => doc.base === base).length;
  // What the screens see: the stored record without its base and text.
  const strip = (doc: StoredDocument): KnowledgeDocument => ({
    id: doc.id,
    name: doc.name,
    size: doc.size,
    updated: doc.updated,
    owner: doc.owner,
    folder: doc.folder,
  });
  const shownFolder = (folder: StoredFolder): KnowledgeFolder => ({
    id: folder.id,
    name: folder.name,
    updated: folder.updated,
    parent: folder.parent,
  });
  // The session lives in memory only. Passwords are accepted and dropped: nothing checks, keeps
  // or forwards them.
  // A demo person is signed in from the start, so local work opens straight into the app.
  let user: User | undefined = {
    id: 'u-asha',
    name: 'Asha Rao',
    email: 'asha@example.org',
    role: 'admin',
  };
  let hasAccount = true;
  // Other people with accounts, the signed-in person's own record, people deleted this session
  // (for Undo) and the admin ledger. Passwords given to addUser or updateUser are dropped.
  const joined = new Date(2026, 10, 3);
  let people: AdminUser[] = [
    {
      id: 'u-admin',
      name: '4CE Administrator',
      email: 'admin@4ce.local',
      role: 'admin',
      created: new Date(2026, 8, 20),
      lastActive: new Date(),
    },
  ];
  const deleted = new Map<string, AdminUser>();
  let groups: Group[] = [];
  const deletedGroups = new Map<string, Group>();
  let defaultPermissions: StoredPermissions = {};
  let feedback: Feedback[] = structuredClone(seeded);
  // The orchestrator pipe the capture account shows, with a short stand-in body.
  const functions: ServerFunction[] = [
    {
      id: 'orchestrator',
      name: '4CE Orchestrator',
      type: 'pipe',
      version: '0.1.0',
      description:
        'TONY routes, FRIDAY grounds, JARVIS executes, ULTRON verifies, a human approves.',
      content: `"""\ntitle: 4CE Orchestrator\nversion: 0.1.0\n"""\n\n\nclass Pipe:\n    def pipe(self, body: dict) -> str:\n        return "The 4CE server runs the six roles."\n`,
      enabled: true,
      updated: new Date(Date.now() - 32 * 86_400_000),
      owner: { name: '4CE Administrator', email: 'admin@4ce.local' },
    },
  ];
  const deletedFeedback = new Map<string, Feedback>();
  const adminSettings = new Map<string, Record<string, unknown>>();
  let notes: Note[] = [];
  let automations: Automation[] = [];
  const deletedAutomations = new Map<string, Automation>();
  let calendars: Calendar[] = [{ id: 'personal', name: 'Personal', color: 'blue' }];
  let events: CalendarEvent[] = [];
  const deletedEvents = new Map<string, CalendarEvent>();
  // One seeded channel with a short exchange, so the channel screen has something to show.
  let channels: Channel[] = [
    { id: 'general', name: 'general', description: 'Everyone', members: ['u-admin', 'u-asha'] },
  ];
  const minutesAgo = (minutes: number) => new Date(Date.now() - minutes * 60_000);
  let channelMessages: ChannelMessage[] = [
    {
      id: 'cm-1',
      channelId: 'general',
      userId: 'u-admin',
      userName: '4CE Administrator',
      content: 'Welcome to the general channel.',
      at: minutesAgo(90),
      pinned: true,
      edited: false,
      reactions: {},
    },
    {
      id: 'cm-2',
      channelId: 'general',
      userId: 'u-admin',
      userName: '4CE Administrator',
      content: 'Share questions for the team here.',
      at: minutesAgo(88),
      pinned: false,
      edited: false,
      reactions: { '👍': ['u-asha'] },
    },
  ];
  const deletedNotes = new Map<string, Note>();
  const ledger: LedgerEntry[] = [];
  const record = (action: string, target: string) =>
    ledger.unshift({ at: new Date(), by: user?.email ?? '', action, target });
  const sameEmail = (a: string, b: string) => a.trim().toLowerCase() === b.trim().toLowerCase();
  const person = (name: string, email: string, role: User['role']): User => ({
    id: `u-${email}`,
    name,
    email,
    role,
  });

  return {
    async currentUser() {
      return user;
    },
    async signIn(email) {
      user = person(email.split('@')[0] || 'Asha Rao', email, 'admin');
      return user;
    },
    async signUp(name, email) {
      user = person(name, email, 'user');
      return user;
    },
    async signOut() {
      user = undefined;
    },
    async setupStatus() {
      return { firstAccount: !hasAccount };
    },
    async createFirstAccount(name, email) {
      hasAccount = true;
      user = person(name, email, 'admin');
      return user;
    },
    // The capture account's workspace: no custom models, 3 knowledge bases, 7 tools.
    async workspaceCounts() {
      return {
        models: models.length,
        knowledge: bases.length,
        prompts: prompts.length,
        skills: skills.length,
        tools: toolList.length,
      };
    },
    async listModels() {
      return [...models];
    },
    async listBaseModels() {
      return BASE_MODELS;
    },
    async listKnowledge() {
      return bases.map((base) => ({ ...base, files: count(base.id) }));
    },
    async getKnowledge(id) {
      const base = bases.find((one) => one.id === id);
      return base && { ...base, files: count(id) };
    },
    async updateKnowledge(id, change) {
      Object.assign(bases.find((one) => one.id === id) ?? {}, change, { updated: new Date() });
    },
    async listContents(base, { folder, query = '', content = false, sort, direction = 'desc' }) {
      const q = query.trim().toLowerCase();
      const hit = (name: string, text = '') =>
        name.toLowerCase().includes(q) || (content && text.toLowerCase().includes(q));
      const inFolder = (item: { base: string; folder?: string; parent?: string }) =>
        item.base === base && (item.folder ?? item.parent) === folder;
      const order = <T extends { name: string; updated: Date }>(list: T[]) => {
        if (!sort) return list;
        const sign = direction === 'asc' ? 1 : -1;
        return [...list].sort((a, b) =>
          sort === 'name'
            ? sign * a.name.localeCompare(b.name)
            : sign * (a.updated.getTime() - b.updated.getTime()),
        );
      };
      const shownFolders = order(folders.filter((one) => inFolder(one) && hit(one.name)));
      const shownDocs = order(docs.filter((one) => inFolder(one) && hit(one.name, one.text)));
      return {
        folders: shownFolders.map(shownFolder),
        documents: shownDocs.map(strip),
        total: shownFolders.length + shownDocs.length,
      };
    },
    async getDocumentText(id) {
      return docs.find((doc) => doc.id === id)?.text ?? '';
    },
    async saveDocumentText(id, text) {
      Object.assign(docs.find((doc) => doc.id === id) ?? {}, { text, updated: new Date() });
    },
    async addDocument(base, { name, text, size, folder }) {
      const doc: StoredDocument = {
        id: crypto.randomUUID(),
        base,
        name,
        text,
        size: size ?? new Blob([text]).size,
        folder,
        updated: new Date(),
        owner: user && { name: user.name, email: user.email },
      };
      docs.unshift(doc);
      return strip(doc);
    },
    async removeDocument(base, id) {
      const at = docs.findIndex((doc) => doc.base === base && doc.id === id);
      if (at >= 0) docs.splice(at, 1);
    },
    async createFolder(base, name, parent) {
      const folder: StoredFolder = {
        id: crypto.randomUUID(),
        base,
        name,
        parent,
        updated: new Date(),
      };
      folders.push(folder);
      return shownFolder(folder);
    },
    async renameItem(base, id, name) {
      const item = [...docs, ...folders].find((one) => one.base === base && one.id === id);
      if (item) item.name = name;
    },
    async deleteFolder(base, id, { contents }) {
      const target = folders.find((one) => one.base === base && one.id === id);
      if (!target) return;
      // Everything below the folder, at any depth.
      const below = new Set([id]);
      for (let grew = true; grew;) {
        grew = false;
        for (const folder of folders)
          if (folder.parent && below.has(folder.parent) && !below.has(folder.id)) {
            below.add(folder.id);
            grew = true;
          }
      }
      if (contents) {
        for (let i = docs.length - 1; i >= 0; i--)
          if (below.has(docs[i].folder ?? '')) docs.splice(i, 1);
        for (let i = folders.length - 1; i >= 0; i--)
          if (below.has(folders[i].id)) folders.splice(i, 1);
      } else {
        for (const doc of docs) if (doc.folder === id) doc.folder = target.parent;
        for (const folder of folders) if (folder.parent === id) folder.parent = target.parent;
        folders.splice(folders.indexOf(target), 1);
      }
    },
    async getUserSettings() {
      return structuredClone(settings);
    },
    async saveUserSettings(change) {
      const copy = structuredClone(change);
      const ui = copy.ui || settings.ui ? { ui: { ...settings.ui, ...copy.ui } } : {};
      settings = { ...settings, ...copy, ...ui };
    },
    async setStatus(status) {
      if (user) user = { ...user, status };
      if (user && !status) delete user.status;
    },
    async activeUsers() {
      return user ? 1 : 0;
    },
    async listMemories() {
      return memories
        .map((one) => ({ ...one }))
        .sort((a, b) => b.updated.getTime() - a.updated.getTime());
    },
    async addMemory(draft) {
      const memory = { ...draft, id: crypto.randomUUID(), updated: stamp() };
      memories.push(memory);
      return { ...memory };
    },
    async updateMemory(id, draft) {
      memories = memories.map((one) =>
        one.id === id ? { ...one, ...draft, updated: stamp() } : one,
      );
    },
    async deleteMemory(id) {
      memories = memories.filter((one) => one.id !== id);
    },
    async clearMemories() {
      memories = [];
    },
    async listPrompts() {
      return prompts.map((one) => ({ ...one }));
    },
    async getPrompt(id) {
      const found = prompt(id);
      return found && { ...found };
    },
    async createPrompt({ name, command, content, tags }) {
      const first: PromptVersion = {
        id: crypto.randomUUID(),
        content,
        message: 'Initial version',
        author: author(),
        created: new Date(),
      };
      const made: Prompt = {
        id: crypto.randomUUID(),
        name,
        command,
        content,
        tags,
        active: true,
        updated: new Date(),
        owner: user && { name: user.name, email: user.email },
        writable: true,
        liveVersion: first.id,
      };
      prompts.unshift(made);
      versions.set(made.id, [first]);
      return { ...made };
    },
    async updatePrompt(id, change) {
      Object.assign(prompt(id) ?? {}, change, { updated: new Date() });
    },
    async setPromptActive(id, active) {
      Object.assign(prompt(id) ?? {}, { active });
    },
    async deletePrompt(id) {
      const at = prompts.findIndex((one) => one.id === id);
      if (at >= 0) prompts.splice(at, 1);
      versions.delete(id);
    },
    async listVersions(id) {
      return [...(versions.get(id) ?? [])];
    },
    async addVersion(id, { content, message, live }) {
      const made: PromptVersion = {
        id: crypto.randomUUID(),
        content,
        message,
        author: author(),
        created: new Date(),
      };
      versions.get(id)?.unshift(made);
      if (live)
        Object.assign(prompt(id) ?? {}, { content, liveVersion: made.id, updated: new Date() });
    },
    async setLiveVersion(id, version) {
      const chosen = versions.get(id)?.find((one) => one.id === version);
      if (chosen)
        Object.assign(prompt(id) ?? {}, { content: chosen.content, liveVersion: chosen.id });
    },
    async deleteVersion(id, version) {
      if (prompt(id)?.liveVersion === version)
        throw new Error('Cannot delete the production version');
      const list = versions.get(id) ?? [];
      const at = list.findIndex((one) => one.id === version);
      if (at >= 0) list.splice(at, 1);
    },
    async resetKnowledge(base) {
      for (let i = docs.length - 1; i >= 0; i--) if (docs[i].base === base) docs.splice(i, 1);
      for (let i = folders.length - 1; i >= 0; i--)
        if (folders[i].base === base) folders.splice(i, 1);
    },
    async createKnowledge(name, description) {
      const made: KnowledgeBase = {
        id: crypto.randomUUID(),
        name,
        description,
        updated: new Date(),
        owner: user && { name: user.name, email: user.email },
        files: 0,
        writable: true,
        source: 'local',
      };
      bases.unshift(made);
      return made;
    },
    async deleteKnowledge(id) {
      bases.splice(
        bases.findIndex((base) => base.id === id),
        1,
      );
    },
    async listTools() {
      return toolList.map((one) => ({ ...one }));
    },
    async getTool(id) {
      const found = tool(id);
      return found && { ...found };
    },
    async createTool({ id, name, description, content }) {
      if (tool(id)) throw new Error(`A tool with the id "${id}" already exists.`);
      const made: Tool = {
        id,
        name,
        description,
        content,
        updated: new Date(),
        owner: user && { name: user.name, email: user.email },
        writable: true,
      };
      toolList.unshift(made);
      return { ...made };
    },
    async updateTool(id, change) {
      Object.assign(tool(id) ?? {}, change, { updated: new Date() });
    },
    async deleteTool(id) {
      const at = toolList.findIndex((one) => one.id === id);
      if (at >= 0) toolList.splice(at, 1);
    },
    async listSkills() {
      return skills.map((one) => ({ ...one }));
    },
    async getSkill(id) {
      const found = skill(id);
      return found && { ...found };
    },
    async createSkill({ id, name, description, instructions }) {
      if (skill(id)) throw new Error(`A skill with the id "${id}" already exists.`);
      const made: Skill = {
        id,
        name,
        description,
        instructions,
        active: true,
        updated: new Date(),
        owner: user && { name: user.name, email: user.email },
        writable: true,
      };
      skills.unshift(made);
      return { ...made };
    },
    async updateSkill(id, change) {
      Object.assign(skill(id) ?? {}, change, { updated: new Date() });
    },
    async setSkillActive(id, active) {
      Object.assign(skill(id) ?? {}, { active });
    },
    async deleteSkill(id) {
      const at = skills.findIndex((one) => one.id === id);
      if (at >= 0) skills.splice(at, 1);
    },
    async saveModel(record) {
      if ([...models, ...BASE_MODELS].some((model) => model.id === record.id)) {
        throw new Error(`The model id "${record.id}" is already in use. Choose another.`);
      }
      const saved = {
        id: record.id,
        name: record.name,
        base: record.base,
        updated: new Date(),
        owner: user && { name: user.name, email: user.email },
        enabled: true,
        hidden: false,
        writable: true,
      };
      models.unshift(saved);
      return saved;
    },
    async listChats(): Promise<ChatSummary[]> {
      return chats
        .filter((chat) => !archived.has(chat.id))
        .sort((a, b) => b.updated.getTime() - a.updated.getTime())
        .map(({ id, title, updated, outcome }) => ({ id, title, updated, outcome }));
    },
    async getChat(id) {
      return chats.find((chat) => chat.id === id);
    },
    async listUsers() {
      const self: AdminUser[] = user ? [{ ...user, created: joined, lastActive: new Date() }] : [];
      return [...self, ...people.map((one) => ({ ...one }))];
    },
    async addUser({ name, email, role }) {
      const taken = [user?.email ?? '', ...people.map((one) => one.email)];
      if (taken.some((one) => sameEmail(one, email))) {
        throw new Error(`An account with ${email} already exists.`);
      }
      const added: AdminUser = {
        id: crypto.randomUUID(),
        name: name.trim(),
        email: email.trim(),
        role,
        created: new Date(),
        lastActive: new Date(),
      };
      people = [...people, added];
      record('user.add', added.email);
      return { ...added };
    },
    async updateUser(id, { name, email, role, avatar }) {
      if (user?.id === id) user = { ...user, name, email, role };
      people = people.map((one) =>
        one.id === id ? { ...one, name, email, role, ...(avatar ? { avatar } : {}) } : one,
      );
      record('user.update', email);
    },
    async deleteUser(id) {
      const found = people.find((one) => one.id === id);
      if (!found) return;
      deleted.set(id, found);
      people = people.filter((one) => one.id !== id);
      record('user.delete', found.email);
    },
    async restoreUser(id) {
      const found = deleted.get(id);
      if (!found) return;
      deleted.delete(id);
      people = [...people, found];
      record('user.restore', found.email);
    },
    // Without groups or access rules yet, everyone reaches every model, base and tool.
    async previewAccess() {
      return {
        groups: [],
        models: BASE_MODELS.map((one) => one.name),
        knowledge: bases.map((one) => one.name),
        tools: toolList.map((one) => one.name),
      };
    },
    async listGroups() {
      return structuredClone(groups);
    },
    async createGroup(draft) {
      const group: Group = { ...structuredClone(draft), id: crypto.randomUUID(), members: [] };
      groups = [...groups, group];
      record('group.add', group.name);
      return structuredClone(group);
    },
    async updateGroup(id, draft) {
      groups = groups.map((one) => (one.id === id ? { ...one, ...structuredClone(draft) } : one));
      record('group.update', draft.name);
    },
    async deleteGroup(id) {
      const found = groups.find((one) => one.id === id);
      if (!found) return;
      deletedGroups.set(id, found);
      groups = groups.filter((one) => one.id !== id);
      record('group.delete', found.name);
    },
    async restoreGroup(id) {
      const found = deletedGroups.get(id);
      if (!found) return;
      deletedGroups.delete(id);
      groups = [...groups, found];
      record('group.restore', found.name);
    },
    async setGroupMember(groupId, userId, member) {
      const group = groups.find((one) => one.id === groupId);
      if (!group || group.members.includes(userId) === member) return;
      group.members = member
        ? [...group.members, userId]
        : group.members.filter((one) => one !== userId);
      record(member ? 'group.member.add' : 'group.member.remove', `${group.name}: ${userId}`);
    },
    async userGroups(userId) {
      return structuredClone(groups.filter((one) => one.members.includes(userId)));
    },
    async getDefaultPermissions() {
      return structuredClone(defaultPermissions);
    },
    async saveDefaultPermissions(permissions) {
      defaultPermissions = structuredClone(permissions);
      record('permissions.defaults', 'user role');
    },
    async leaderboard() {
      return standings(feedback);
    },
    async listFeedback() {
      return structuredClone(feedback).sort((a, b) => b.updated.getTime() - a.updated.getTime());
    },
    async deleteFeedback(id) {
      const found = feedback.find((one) => one.id === id);
      if (!found) return;
      deletedFeedback.set(id, found);
      feedback = feedback.filter((one) => one.id !== id);
      record('feedback.delete', `${found.modelId}: ${id}`);
    },
    async restoreFeedback(id) {
      const found = deletedFeedback.get(id);
      if (!found) return;
      deletedFeedback.delete(id);
      feedback = [...feedback, found];
      record('feedback.restore', `${found.modelId}: ${id}`);
    },
    async modelActivity(modelId, days) {
      const mine = feedback.filter(
        (one) => one.modelId === modelId || one.siblings.includes(modelId),
      );
      const first = mine.reduce((min, one) => Math.min(min, one.created.getTime()), Date.now());
      const count = days || Math.max(1, Math.ceil((Date.now() - first) / 86_400_000) + 1);
      return Array.from({ length: count }, (_, index) => {
        const day = new Date(Date.now() - (count - 1 - index) * 86_400_000)
          .toISOString()
          .slice(0, 10);
        const that = mine.filter((one) => one.created.toISOString().slice(0, 10) === day);
        const won = that.filter(
          (one) => (one.modelId === modelId) === (one.result === 1) && one.result !== 0,
        ).length;
        return { date: day, won, lost: that.filter((one) => one.result !== 0).length - won };
      });
    },
    async listFunctions() {
      return structuredClone(functions);
    },
    async getFunction(id) {
      const found = functions.find((one) => one.id === id);
      return found && structuredClone(found);
    },
    async getAdminSettings(panel) {
      return structuredClone(adminSettings.get(panel) ?? {});
    },
    async saveAdminSettings(panel, values) {
      adminSettings.set(panel, { ...adminSettings.get(panel), ...structuredClone(values) });
      record(`settings.${panel}`, Object.keys(values).join(', '));
    },
    async exportAdminData(kind) {
      if (kind === 'database') return undefined;
      record(`export.${kind}`, kind);
      if (kind === 'config') return JSON.stringify(Object.fromEntries(adminSettings));
      if (kind === 'chats') return JSON.stringify(chats);
      const everyone = [...(user ? [user] : []), ...people];
      const cell = (value: string) =>
        /[",\n]/.test(value) ? `"${value.replaceAll('"', '""')}"` : value;
      return [
        'id,name,email,role',
        ...everyone.map((one) => [one.id, one.name, one.email, one.role].map(cell).join(',')),
      ].join('\n');
    },
    async importAdminConfig(config) {
      const previous = structuredClone(Object.fromEntries(adminSettings));
      adminSettings.clear();
      for (const [panel, values] of Object.entries(structuredClone(config)))
        adminSettings.set(panel, values);
      record('config.import', Object.keys(config).join(', '));
      return previous;
    },
    // The fake keeps no uploads or vectors; it only records the request.
    async adminMaintenance(task) {
      record(`maintenance.${task}`, task);
    },
    // A small fixed week: three answers from the orchestrator to the administrator.
    async getAnalytics(days) {
      const span = (days || 7) + 1;
      const active: Record<number, number> = { 6: 1, 3: 2 };
      const today = Date.UTC(
        new Date().getUTCFullYear(),
        new Date().getUTCMonth(),
        new Date().getUTCDate(),
      );
      return {
        totals: { messages: 3, tokens: 4400, chats: 2, users: 1 },
        daily: Array.from({ length: span }, (_, index) => {
          const ago = span - 1 - index;
          return {
            date: new Date(today - ago * 86_400_000).toISOString().slice(0, 10),
            messages: active[ago] ?? 0,
          };
        }),
        models: [
          { id: '4ce-tony', name: '4CE / TONY (Orchestrator)', messages: 3, users: 1, chats: 2 },
        ],
        users: [{ id: 'u-admin', name: '4CE Administrator', messages: 3, tokens: 4400 }],
      };
    },
    async listNotes() {
      return structuredClone(notes).sort((a, b) => b.updated.getTime() - a.updated.getTime());
    },
    async getNote(id) {
      const found = notes.find((one) => one.id === id);
      return found && structuredClone(found);
    },
    async createNote({ title, content }) {
      const now = new Date();
      const note: Note = {
        id: crypto.randomUUID(),
        title,
        content,
        created: now,
        updated: now,
        owner: { name: user?.name ?? '', email: user?.email ?? '' },
      };
      notes = [...notes, note];
      return structuredClone(note);
    },
    async updateNote(id, { title, content }) {
      notes = notes.map((one) =>
        one.id === id ? { ...one, title, content, updated: new Date() } : one,
      );
    },
    async deleteNote(id) {
      const found = notes.find((one) => one.id === id);
      if (!found) return;
      deletedNotes.set(id, found);
      notes = notes.filter((one) => one.id !== id);
    },
    async restoreNote(id) {
      const found = deletedNotes.get(id);
      if (!found) return;
      deletedNotes.delete(id);
      notes = [...notes, found];
    },
    // A stand-in rewrite: the text tidied into sentences, sent a few words at a time.
    async *enhanceNote(content, signal) {
      const tidy = content
        .split(/\n+/)
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => line.charAt(0).toUpperCase() + line.slice(1).replace(/[.!?]?$/, '.'))
        .join('\n\n');
      for (const word of (tidy || 'Nothing to enhance yet.').split(/(?<= )/)) {
        if (signal?.aborted) return;
        if (pace) await new Promise((done) => setTimeout(done, 30 * pace));
        yield word;
      }
    },
    async listChannels() {
      return structuredClone(channels);
    },
    async getChannel(id) {
      const found = channels.find((one) => one.id === id);
      return found && structuredClone(found);
    },
    async createChannel({ name, description }) {
      const channel: Channel = {
        id: crypto.randomUUID(),
        name: name.trim().toLowerCase().replace(/\s+/g, '-'),
        description,
        members: user ? [user.id] : [],
      };
      channels = [...channels, channel];
      record('channel.add', channel.name);
      return structuredClone(channel);
    },
    async deleteChannel(id) {
      const found = channels.find((one) => one.id === id);
      if (!found) return;
      channels = channels.filter((one) => one.id !== id);
      channelMessages = channelMessages.filter((one) => one.channelId !== id);
      record('channel.delete', found.name);
    },
    async listChannelMessages(channelId) {
      return structuredClone(channelMessages.filter((one) => one.channelId === channelId));
    },
    async sendChannelMessage(channelId, { content, replyTo, threadId }) {
      const message: ChannelMessage = {
        id: crypto.randomUUID(),
        channelId,
        userId: user?.id ?? '',
        userName: user?.name ?? '',
        content,
        at: new Date(),
        pinned: false,
        edited: false,
        reactions: {},
        replyTo,
        threadId,
      };
      channelMessages = [...channelMessages, message];
      return structuredClone(message);
    },
    async editChannelMessage(id, content) {
      channelMessages = channelMessages.map((one) =>
        one.id === id ? { ...one, content, edited: true } : one,
      );
    },
    async deleteChannelMessage(id) {
      channelMessages = channelMessages.filter((one) => one.id !== id);
    },
    async pinChannelMessage(id, pinned) {
      channelMessages = channelMessages.map((one) => (one.id === id ? { ...one, pinned } : one));
    },
    async reactChannelMessage(id, emoji) {
      const me = user?.id ?? '';
      channelMessages = channelMessages.map((one) => {
        if (one.id !== id) return one;
        const who = one.reactions[emoji] ?? [];
        const next = who.includes(me) ? who.filter((name) => name !== me) : [...who, me];
        const reactions = { ...one.reactions, [emoji]: next };
        if (!next.length) delete reactions[emoji];
        return { ...one, reactions };
      });
    },
    // Presence is simulated: the other member types now and then.
    async channelTyping() {
      return Math.floor(Date.now() / 7000) % 3 === 0 ? ['4CE Administrator'] : [];
    },
    // Stand-in model output for the playground, sent a few words at a time.
    async *playgroundStream(input, signal) {
      const last = input.kind === 'chat' ? (input.messages.at(-1)?.content ?? '') : input.prompt;
      const text =
        input.kind === 'chat'
          ? `This is a sample reply from ${input.model || 'the model'} to: "${last.slice(0, 80)}".`
          : ' and the text carries on from where the prompt stopped, one phrase at a time.';
      for (const word of text.split(/(?<= )/)) {
        if (signal?.aborted) return;
        if (pace) await new Promise((done) => setTimeout(done, 30 * pace));
        yield word;
      }
    },
    async listCalendars() {
      return structuredClone(calendars);
    },
    async createCalendar({ name, color }) {
      const calendar = { id: crypto.randomUUID(), name, color };
      calendars = [...calendars, calendar];
      return { ...calendar };
    },
    async listEvents() {
      return structuredClone(events);
    },
    async saveEvent(event) {
      const saved: CalendarEvent = {
        ...structuredClone(event),
        id: event.id ?? crypto.randomUUID(),
      };
      events = [...events.filter((one) => one.id !== saved.id), saved];
      return structuredClone(saved);
    },
    async deleteEvent(id) {
      const found = events.find((one) => one.id === id);
      if (!found) return;
      deletedEvents.set(id, found);
      events = events.filter((one) => one.id !== id);
    },
    async restoreEvent(id) {
      const found = deletedEvents.get(id);
      if (!found) return;
      deletedEvents.delete(id);
      events = [...events, found];
    },
    async listAutomations() {
      return structuredClone(automations);
    },
    async getAutomation(id) {
      const found = automations.find((one) => one.id === id);
      return found && structuredClone(found);
    },
    async saveAutomation(draft) {
      const before = automations.find((one) => one.id === draft.id);
      const saved: Automation = {
        ...structuredClone(draft),
        id: draft.id ?? crypto.randomUUID(),
        runs: before?.runs ?? [],
      };
      automations = before
        ? automations.map((one) => (one.id === saved.id ? saved : one))
        : [...automations, saved];
      return structuredClone(saved);
    },
    async deleteAutomation(id) {
      const found = automations.find((one) => one.id === id);
      if (!found) return;
      deletedAutomations.set(id, found);
      automations = automations.filter((one) => one.id !== id);
    },
    async restoreAutomation(id) {
      const found = deletedAutomations.get(id);
      if (!found) return;
      deletedAutomations.delete(id);
      automations = [...automations, found];
    },
    async runAutomation(id) {
      automations = automations.map((one) =>
        one.id === id
          ? { ...one, runs: [{ at: new Date(), chatId: CHATS[0]?.id }, ...one.runs] }
          : one,
      );
    },
    // Only the signed-in person has chats in the fake.
    async userChats(id) {
      return id === user?.id ? this.listChats() : [];
    },
    async adminLedger() {
      return ledger.map((entry) => ({ ...entry }));
    },
    async getProfile() {
      return structuredClone({ ...profile, name: user?.name ?? '' });
    },
    async saveProfile({ name, ...rest }) {
      profile = structuredClone(rest);
      if (user) user = { ...user, name };
    },
    // The fake cannot check the current password; it only refuses a missing one. Neither
    // password is kept.
    async changePassword(current, next) {
      if (!current || !next) throw new Error('Enter your current and new password.');
    },
    async getUsage() {
      return usage();
    },
    async exportChats() {
      return structuredClone(chats);
    },
    async importChats(list) {
      const added = list.map((one) => ({
        id: crypto.randomUUID(),
        title: one.title,
        messages: structuredClone(one.messages),
        updated: new Date(),
      }));
      chats = [...added, ...chats];
      return added.length;
    },
    async archiveAllChats() {
      for (const chat of chats) archived.add(chat.id);
    },
    async listArchivedChats() {
      return chats
        .filter((chat) => archived.has(chat.id))
        .sort((a, b) => b.updated.getTime() - a.updated.getTime())
        .map(({ id, title, updated, outcome }) => ({ id, title, updated, outcome }));
    },
    async unarchiveChat(id) {
      archived.delete(id);
    },
    async unarchiveAllChats() {
      archived.clear();
    },
    async deleteChat(id) {
      chats = chats.filter((chat) => chat.id !== id);
      archived.delete(id);
    },
    async deleteAllChats() {
      chats = [];
      archived.clear();
    },
    ask(_chatId, question, signal) {
      // A question about the server being down replays a run that stops at the Analyst, so the
      // run error card can be seen without a backend.
      if (/server down/i.test(question)) return replay(failing(), pace, signal);
      // A question about rounding replays a run the Challenger sends back once.
      if (/rounded/i.test(question)) return replay(replanned(), pace, signal);
      return replay(script(), pace, signal);
    },
    decide(_chatId, outcome, by, signal) {
      return replay(closing(outcome, by), pace, signal);
    },
  };
}
