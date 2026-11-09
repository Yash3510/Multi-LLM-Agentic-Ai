// A fake data source for building the screens before the 4CE API exists: a few stored chats and
// a scripted answer replayed with realistic pacing. Nothing leaves the browser. The content is
// sector-neutral (rules R2 to R6, ids like CASE-0142).
import type {
  Chat,
  ChatSummary,
  DataSource,
  KnowledgeBase,
  KnowledgeDocument,
  KnowledgeFolder,
  Prompt,
  PromptVersion,
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

function closing(outcome: 'released' | 'withheld', by: string): Step[] {
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
const TOOLS: WorkspaceItem[] = [
  'Sovereignty Check',
  'Threshold Check',
  'Engineering Calculations',
  'Workspace Files',
  'Spreadsheets',
  'Sovereign Sandbox',
  'Deliverables',
].map((name) => ({ id: name.toLowerCase().replace(/ /g, '-'), name: `4CE ${name}` }));

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

export function createFakeSource({ pace = 1 }: { pace?: number } = {}): DataSource {
  const models: WorkspaceModel[] = [];
  const bases = knowledge();
  const docs = documents();
  const folders: StoredFolder[] = [];
  const prompts: Prompt[] = [];
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
        skills: 0,
        tools: TOOLS.length,
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
      return TOOLS;
    },
    async listSkills() {
      return [];
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
      // A question about rounding replays a run the Challenger sends back once.
      if (/rounded/i.test(question)) return replay(replanned(), pace, signal);
      return replay(script(), pace, signal);
    },
    decide(_chatId, outcome, by, signal) {
      return replay(closing(outcome, by), pace, signal);
    },
  };
}
