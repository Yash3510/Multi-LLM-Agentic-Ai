// The web app's data contract (docs/architecture/web-data-contract.md). Screens read only these
// types; a source (the fake replay today, the 4CE API later) produces them.

/** The six run roles. The stage rail draws all but Reader, as the running app does. */
export type Role = 'planner' | 'reader' | 'analyst' | 'author' | 'challenger' | 'sign-off';

/** How a chat's last run ended: its sidebar marker. */
export type Outcome = 'released' | 'withheld' | 'interrupted' | 'done' | 'direct';

export interface ChatSummary {
  id: string;
  title: string;
  updated: Date;
  outcome?: Outcome;
}

export interface Source {
  /** The citation number shown as [n]. */
  index: number;
  title: string;
  /** The cited passage. */
  passage: string;
}

export interface ToolCall {
  id: string;
  name: string;
  input: string;
  output?: string;
  state: 'running' | 'done' | 'failed';
}

export interface Revision {
  /** The try this draft is (2 after one send-back). */
  try: number;
  /** What the reviewer objected to on the previous try. */
  objections: { by: string; text: string }[];
  /** Lines rewritten, added or taken out since the previous try. */
  changes: { removed?: string; added?: string }[];
}

export interface SignOffRequest {
  /** What was checked, each with its verdict and the citation numbers it rests on. */
  checks: { label: string; verdict: 'pass' | 'review' | 'fail'; cites?: number[] }[];
  /** Present when this draft is a later try after a send-back. */
  revision?: Revision;
}

export interface Receipt {
  /** The run's fingerprint, shown short. */
  fingerprint: string;
  model: string;
  seconds: number;
  sources: number;
  signedBy?: string;
  /** Connections that left the machine during the run, as observed. */
  externalCalls?: number;
  /** Folds under the receipt: full provenance and each agent's own output, as markdown. */
  folds?: { title: string; body: string }[];
}

export interface Message {
  id: string;
  role: 'user' | 'response';
  text: string;
  at: Date;
  /** Status events of the run that produced a response, in arrival order. */
  events?: StreamEvent[];
  /** The response is complete (streamed to the end, stopped or failed). */
  finished?: boolean;
  /** A direct reply (no agent chain): its status line and the model that answered. */
  direct?: { status: string; model: string; seconds: number };
}

export interface Chat extends ChatSummary {
  messages: Message[];
}

/**
 * One event of a running answer, in arrival order. `at` is the server's time in milliseconds.
 * Status events carry the stage that is speaking and whether that stage is done.
 */
export type StreamEvent =
  | { type: 'status'; at: number; stage: Role | 'replan'; description: string; done?: boolean }
  | { type: 'delta'; at: number; text: string }
  | { type: 'tool'; at: number; call: ToolCall }
  | { type: 'source'; at: number; source: Source }
  | { type: 'sign-off'; at: number; request: SignOffRequest }
  | { type: 'decision'; at: number; outcome: 'released' | 'withheld'; by: string }
  | { type: 'receipt'; at: number; receipt: Receipt }
  | { type: 'done'; at: number }
  | { type: 'stopped'; at: number }
  | { type: 'error'; at: number; message: string; advice?: string };

/** The signed-in person. `pending` accounts wait for an admin to approve them. */
export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'pending';
  /** A short status the person set from the user menu. */
  status?: { emoji?: string; message?: string };
}

/** The workspace tabs, in the running app's order. */
export type WorkspaceTab = 'models' | 'knowledge' | 'prompts' | 'skills' | 'tools';

/** A custom model in the workspace (a preset over a base model). */
export interface WorkspaceModel {
  id: string;
  name: string;
  /** The model it builds on. */
  base?: string;
  description?: string;
  updated: Date;
  owner?: { name: string; email?: string };
  /** Switched on for chats. */
  enabled: boolean;
  /** Hidden from the model picker. */
  hidden: boolean;
  /** The person may change it. */
  writable: boolean;
  avatar?: string;
}

/** A workspace item offered in a picker: a base model, knowledge base, tool or skill. */
export interface WorkspaceItem {
  id: string;
  name: string;
  description?: string;
}

/** A knowledge base: documents models and chats can retrieve from (workspace F60). */
export interface KnowledgeBase extends WorkspaceItem {
  updated: Date;
  owner?: { name: string; email?: string };
  /** How many files it holds, when the server says. */
  files?: number;
  /** The person may change it. */
  writable: boolean;
  /** Local, or read from an outside source. */
  source: 'local' | 'connected';
  provider?: string;
  sourceName?: string;
  auth?: string;
  meta?: Record<string, string>;
}

/** A document in a knowledge base (workspace F75). */
export interface KnowledgeDocument {
  id: string;
  name: string;
  /** In bytes, when known. */
  size?: number;
  updated: Date;
  owner?: { name: string; email?: string };
  folder?: string;
}

/** A folder inside a knowledge base (F76). */
export interface KnowledgeFolder {
  id: string;
  name: string;
  updated: Date;
  parent?: string;
}

/** Which documents to show: one folder's, matching a search in names (and text, when asked). */
export interface ContentQuery {
  folder?: string;
  query?: string;
  content?: boolean;
  sort?: 'name' | 'created' | 'updated';
  direction?: 'asc' | 'desc';
}

/** A saved prompt, used in chat as a slash command (workspace F88 to F99). */
export interface Prompt {
  id: string;
  name: string;
  /** Without the slash. */
  command: string;
  /** The live version's text. */
  content: string;
  tags: string[];
  active: boolean;
  updated: Date;
  owner?: { name: string; email?: string };
  writable: boolean;
  liveVersion: string;
}

/** One saved version of a prompt's text (F96). */
export interface PromptVersion {
  id: string;
  content: string;
  message?: string;
  author: { name: string };
  created: Date;
}

/** A skill: named markdown instructions a model or chat can switch on (workspace F100 to F106). */
export interface Skill extends WorkspaceItem {
  instructions: string;
  active: boolean;
  updated: Date;
  owner?: { name: string; email?: string };
  writable: boolean;
}

/** A tool: Python code a model can call (workspace F107 to F116). */
export interface Tool extends WorkspaceItem {
  /** The Python source. */
  content: string;
  /** From the code's header, when it names one. */
  version?: string;
  updated: Date;
  owner?: { name: string; email?: string };
  writable: boolean;
}

/** The person's own settings (chat-composer F91 to F104); each page saves its part. */
export interface UserSettings {
  /** The system prompt for new chats. */
  system?: string;
  /** Advanced model parameters left at Default are absent. */
  params?: Record<string, number | string | boolean>;
  /** Interface, notification and audio choices, by key. */
  ui?: Record<string, unknown>;
}

/** Something the assistant remembers about the person (chat-composer F98). */
export interface Memory {
  id: string;
  content: string;
  /** A fact about the person, or lasting context for later chats. */
  type: 'user' | 'context';
  path?: string;
  updated: Date;
}

export type MemoryDraft = Pick<Memory, 'content' | 'type' | 'path'>;

/** One day (or the week or running total it stands for) in the usage heat map. */
export interface UsageDay {
  /** YYYY-MM-DD. */
  date: string;
  messages: number;
  chats: number;
  tokens: number;
  /** Messages per model id. */
  models: Record<string, number>;
}

/** The person's own usage (chat-composer F101); token counts are estimates. */
export interface Usage {
  totals: {
    lifetimeTokens: number;
    peakDailyTokens: number;
    longestChatSeconds: number;
    currentStreak: number;
    longestStreak: number;
    totalChats: number;
    modelsUsed: number;
    messages: number;
    userMessages: number;
    assistantMessages: number;
  };
  /** Oldest first, one entry per day. */
  daily: UsageDay[];
  /** One entry per week, dated by its Monday. */
  weekly: UsageDay[];
  /** One running total per day. */
  cumulative: UsageDay[];
  insights: {
    averageTokensPerChat: number;
    averageMessagesPerActiveDay: number;
    userMessageShare: number;
    assistantMessageShare: number;
  };
  topModels: { id: string; messages: number; tokens: number }[];
  topTools: { name: string; count: number }[];
}

/** What the model editor saves (the API takes the full record; see web-data-contract.md). */
export interface ModelRecord {
  id: string;
  name: string;
  base: string;
  params?: Record<string, unknown>;
  meta?: Record<string, unknown>;
}

/** Where screens get their data. The fake replay implements it now; the API client later. */
export interface DataSource {
  /** The person signed in on this device, or undefined. */
  currentUser(): Promise<User | undefined>;
  /** The password goes only to the backend: never logged, stored or put in a URL. */
  signIn(email: string, password: string): Promise<User>;
  signUp(name: string, email: string, password: string): Promise<User>;
  signOut(): Promise<void>;
  /** Whether the server has no account yet, so the first sign-up creates the admin. */
  setupStatus(): Promise<{ firstAccount: boolean }>;
  createFirstAccount(name: string, email: string, password: string): Promise<User>;
  listChats(): Promise<ChatSummary[]>;
  getUserSettings(): Promise<UserSettings>;
  /** Merges the given parts into the saved settings; interface choices merge by key. */
  saveUserSettings(change: UserSettings): Promise<void>;
  /** Sets or, with undefined, clears the person's status. */
  setStatus(status: { emoji?: string; message?: string } | undefined): Promise<void>;
  /** How many people are signed in now. */
  activeUsers(): Promise<number>;
  getUsage(): Promise<Usage>;
  /** Every chat with its messages, archived ones included, for a JSON export. */
  exportChats(): Promise<Chat[]>;
  /** Adds chats from an export; returns how many were added. */
  importChats(chats: Pick<Chat, 'title' | 'messages'>[]): Promise<number>;
  /** Moves every chat into the archive. */
  archiveAllChats(): Promise<void>;
  deleteAllChats(): Promise<void>;
  /** The person's memories, most recently changed first. */
  listMemories(): Promise<Memory[]>;
  addMemory(draft: MemoryDraft): Promise<Memory>;
  updateMemory(id: string, draft: MemoryDraft): Promise<void>;
  deleteMemory(id: string): Promise<void>;
  clearMemories(): Promise<void>;
  /** How many items each workspace tab holds. */
  workspaceCounts(): Promise<Record<WorkspaceTab, number>>;
  listModels(): Promise<WorkspaceModel[]>;
  /** The models a custom model can build on. */
  listBaseModels(): Promise<WorkspaceItem[]>;
  listKnowledge(): Promise<KnowledgeBase[]>;
  /** Creates a private knowledge base. */
  createKnowledge(name: string, description: string): Promise<KnowledgeBase>;
  deleteKnowledge(id: string): Promise<void>;
  getKnowledge(id: string): Promise<KnowledgeBase | undefined>;
  updateKnowledge(id: string, change: { name: string; description: string }): Promise<void>;
  /** One folder's subfolders and documents, folders first. */
  listContents(
    base: string,
    query: ContentQuery,
  ): Promise<{ folders: KnowledgeFolder[]; documents: KnowledgeDocument[]; total: number }>;
  getDocumentText(id: string): Promise<string>;
  saveDocumentText(id: string, text: string): Promise<void>;
  /** Adds a document from text or an uploaded file's extracted text. */
  addDocument(
    base: string,
    file: { name: string; text: string; size?: number; folder?: string },
  ): Promise<KnowledgeDocument>;
  /** Removes a document from this base; the stored file stays. */
  removeDocument(base: string, id: string): Promise<void>;
  createFolder(base: string, name: string, parent?: string): Promise<KnowledgeFolder>;
  renameItem(base: string, id: string, name: string): Promise<void>;
  /** Deletes a folder with everything in it, or moves its contents up to its parent. */
  deleteFolder(base: string, id: string, options: { contents: boolean }): Promise<void>;
  /** Removes every document and folder from the base. */
  resetKnowledge(base: string): Promise<void>;
  listPrompts(): Promise<Prompt[]>;
  getPrompt(id: string): Promise<Prompt | undefined>;
  /** Creates a prompt; its first version is live. */
  createPrompt(draft: {
    name: string;
    command: string;
    content: string;
    tags: string[];
  }): Promise<Prompt>;
  updatePrompt(
    id: string,
    change: { name: string; command: string; tags: string[] },
  ): Promise<void>;
  setPromptActive(id: string, active: boolean): Promise<void>;
  deletePrompt(id: string): Promise<void>;
  /** Newest first. */
  listVersions(id: string): Promise<PromptVersion[]>;
  addVersion(
    id: string,
    version: { content: string; message?: string; live: boolean },
  ): Promise<void>;
  setLiveVersion(id: string, version: string): Promise<void>;
  /** Rejects for the live version. */
  deleteVersion(id: string, version: string): Promise<void>;
  listTools(): Promise<Tool[]>;
  getTool(id: string): Promise<Tool | undefined>;
  /** Creates a tool; rejects when the id is taken. */
  createTool(draft: {
    id: string;
    name: string;
    description: string;
    content: string;
  }): Promise<Tool>;
  updateTool(
    id: string,
    change: { name: string; description: string; content: string },
  ): Promise<void>;
  deleteTool(id: string): Promise<void>;
  /** Every skill the person can see, switched off ones too. */
  listSkills(): Promise<Skill[]>;
  getSkill(id: string): Promise<Skill | undefined>;
  /** Creates a skill, switched on; rejects when the id is taken. */
  createSkill(draft: {
    id: string;
    name: string;
    description: string;
    instructions: string;
  }): Promise<Skill>;
  updateSkill(
    id: string,
    change: { name: string; description: string; instructions: string },
  ): Promise<void>;
  setSkillActive(id: string, active: boolean): Promise<void>;
  deleteSkill(id: string): Promise<void>;
  /** Creates a custom model; rejects when the id is taken. */
  saveModel(model: ModelRecord): Promise<WorkspaceModel>;
  getChat(id: string): Promise<Chat | undefined>;
  /** Asks a question in a chat and yields the answer's events as they arrive. */
  ask(chatId: string, question: string, signal?: AbortSignal): AsyncIterable<StreamEvent>;
  /** Records the person's sign-off decision and yields the rest of the run. */
  decide(
    chatId: string,
    outcome: 'released' | 'withheld',
    by: string,
    signal?: AbortSignal,
  ): AsyncIterable<StreamEvent>;
}
