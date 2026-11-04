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

export interface SignOffRequest {
  /** What was checked, each with its verdict. */
  checks: { label: string; verdict: 'pass' | 'review' | 'fail' }[];
}

export interface Receipt {
  /** The run's fingerprint, shown short. */
  fingerprint: string;
  model: string;
  seconds: number;
  sources: number;
  signedBy?: string;
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

/** Where screens get their data. The fake replay implements it now; the API client later. */
export interface DataSource {
  listChats(): Promise<ChatSummary[]>;
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
