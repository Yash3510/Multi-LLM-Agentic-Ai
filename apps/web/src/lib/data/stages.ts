// The stage rail's state, derived only from a run's events (own-4ce features F20), so it shows
// what actually happened and survives a reload.
import type { Role, Source, StreamEvent, ToolCall } from './types';

/** The rail's nodes, in order. Reader works inside the Analyst's stage, as in the running app. */
export const RAIL = ['planner', 'analyst', 'author', 'challenger', 'sign-off'] as const;
export type RailStage = (typeof RAIL)[number];

export type StageState =
  | 'pending'
  | 'skipped'
  | 'active'
  | 'interrupted'
  | 'requeued'
  | 'fail'
  | 'released'
  | 'withheld'
  | 'done';

export interface StageView {
  state: StageState;
  /** Time spent in the stage across all passes, in milliseconds; 0 when it never ran. */
  ms: number;
  /** How many times the stage ran. */
  passes: number;
  note?:
    | 'stopped'
    | 'failed'
    | 'interrupted'
    | 'reviewing'
    | 'released'
    | 'withheld'
    | 'returned'
    | 'fail';
}

export interface RunView {
  /** Drawn only when the chain ran (an Analyst, Author or Challenger event). */
  rail: boolean;
  stages: Record<RailStage, StageView>;
  replans: number;
  /** The agents' time, without the person's wait at sign-off. */
  workingMs: number;
  running: boolean;
}

interface Segment {
  stage: Role;
  start: number;
  end?: number;
  pass: number;
}

const AGAIN = new Set<Role>(['analyst', 'author', 'challenger']);

/** <0.1s, then one decimal under a minute, then minutes and zero-padded seconds. */
export function formatStageTime(ms: number): string {
  if (ms < 100) return '<0.1s';
  const tenths = Math.round(ms / 100);
  if (tenths < 600) return `${(tenths / 10).toFixed(1)}s`;
  const seconds = Math.round(ms / 1000);
  return `${Math.floor(seconds / 60)}m ${String(seconds % 60).padStart(2, '0')}s`;
}

export function deriveRun(events: StreamEvent[], finished: boolean, now: number): RunView {
  const segments: Segment[] = [];
  let replans = 0;
  let challengerFailed = false;
  let outcome: 'released' | 'withheld' | undefined;
  // A withheld decision with a reason went back to whoever asked: the node notes a return.
  let returned = false;
  let endedBy: { stage: Role; note: 'stopped' | 'failed' } | undefined;
  const open = () => {
    const last = segments.at(-1);
    return last && last.end === undefined ? last : undefined;
  };
  const close = (at: number) => {
    const segment = open();
    if (segment) segment.end = at;
  };

  for (const event of events) {
    if (event.type === 'status') {
      if (event.stage === 'replan') {
        replans += 1;
        close(event.at);
        continue;
      }
      if (open()?.stage !== event.stage) {
        close(event.at);
        segments.push({ stage: event.stage, start: event.at, pass: replans });
      }
      if (event.stage === 'challenger') {
        const words = event.description.toLowerCase();
        if (/\bfail/.test(words)) challengerFailed = true;
        else if (/\bpass/.test(words)) challengerFailed = false;
      }
      if (event.done) close(event.at);
    } else if (event.type === 'decision') {
      outcome = event.outcome;
      returned = Boolean(event.reason);
      close(event.at);
    } else if (event.type === 'done') {
      if (!outcome && segments.at(-1)?.stage === 'sign-off') outcome = 'released';
      close(event.at);
    } else if (event.type === 'stopped' || event.type === 'error') {
      const segment = open() ?? segments.at(-1);
      if (segment)
        endedBy = { stage: segment.stage, note: event.type === 'stopped' ? 'stopped' : 'failed' };
      close(event.at);
    }
  }

  const last = segments.at(-1);
  const lastOpen = last && last.end === undefined ? last : undefined;
  const running = !finished && lastOpen !== undefined;

  const view = (stage: RailStage): StageView => {
    const own = segments.filter((segment) => segment.stage === stage);
    const ms = own.reduce(
      (sum, segment) => sum + ((segment.end ?? (running ? now : segment.start)) - segment.start),
      0,
    );
    const passes = own.length;
    if (!passes) return { state: finished || outcome ? 'skipped' : 'pending', ms: 0, passes };
    if (running && lastOpen?.stage === stage)
      return { state: 'active', ms, passes, note: stage === 'sign-off' ? 'reviewing' : undefined };
    if (finished && lastOpen?.stage === stage)
      return { state: 'interrupted', ms, passes, note: 'interrupted' };
    if (endedBy?.stage === stage) return { state: 'interrupted', ms, passes, note: endedBy.note };
    if (running && AGAIN.has(stage) && (own.at(-1)?.pass ?? replans) < replans)
      return { state: 'requeued', ms, passes };
    if (stage === 'challenger' && challengerFailed)
      return { state: 'fail', ms, passes, note: 'fail' };
    if (stage === 'sign-off' && outcome)
      return { state: outcome, ms, passes, note: returned ? 'returned' : outcome };
    return { state: 'done', ms, passes };
  };

  const stages = {
    planner: view('planner'),
    analyst: view('analyst'),
    author: view('author'),
    challenger: view('challenger'),
    'sign-off': view('sign-off'),
  };
  // Every agent's time, Reader's included, without the person's wait at sign-off.
  const workingMs = segments
    .filter((segment) => segment.stage !== 'sign-off')
    .reduce(
      (sum, segment) => sum + ((segment.end ?? (running ? now : segment.start)) - segment.start),
      0,
    );
  return {
    rail: segments.some((segment) => AGAIN.has(segment.stage)),
    stages,
    replans,
    workingMs,
    running,
  };
}

/** What one rail stage did, from the run's events: the run view's stage detail. */
export interface StageDetail {
  /** Its status lines, each with the time since the run started and the try it belongs to. */
  lines: { ms: number; role: Role | 'replan'; text: string; try: number }[];
  /** Tool calls made while it worked, each at its latest state. */
  calls: ToolCall[];
  /** Sources found while it worked, once each. */
  sources: Source[];
  /** The text it drafted. */
  text: string;
}

/** Each role's node on the rail: Reader works inside the Analyst's stage. */
const NODE: Record<Role, RailStage> = {
  planner: 'planner',
  reader: 'analyst',
  analyst: 'analyst',
  author: 'author',
  challenger: 'challenger',
  'sign-off': 'sign-off',
};

/** Events between two status lines belong to the stage of the first; a replan line belongs to
 * the stage that sent the work back, and every line after it to the next try. */
export function stageDetails(events: StreamEvent[]): Record<RailStage, StageDetail> {
  const empty = (): StageDetail => ({ lines: [], calls: [], sources: [], text: '' });
  const details: Record<RailStage, StageDetail> = {
    planner: empty(),
    analyst: empty(),
    author: empty(),
    challenger: empty(),
    'sign-off': empty(),
  };
  const start = events[0]?.at ?? 0;
  let current: StageDetail | undefined;
  let tries = 1;
  for (const event of events) {
    if (event.type === 'status') {
      if (event.stage !== 'replan') current = details[NODE[event.stage]];
      current?.lines.push({
        ms: event.at - start,
        role: event.stage,
        text: event.description,
        try: tries,
      });
      if (event.stage === 'replan') tries += 1;
    } else if (current && event.type === 'tool') {
      const known = current.calls.findIndex((call) => call.id === event.call.id);
      if (known >= 0) current.calls[known] = event.call;
      else current.calls.push(event.call);
    } else if (current && event.type === 'source') {
      if (!current.sources.some((source) => source.index === event.source.index))
        current.sources.push(event.source);
    } else if (current && event.type === 'delta') {
      current.text += event.text;
    }
  }
  return details;
}
