// The stage rail's state, derived only from a run's events (own-4ce features F20), so it shows
// what actually happened and survives a reload.
import type { Role, StreamEvent } from './types';

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
  note?: 'stopped' | 'failed' | 'interrupted' | 'reviewing' | 'released' | 'withheld' | 'fail';
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
    if (stage === 'sign-off' && outcome) return { state: outcome, ms, passes, note: outcome };
    return { state: 'done', ms, passes };
  };

  const stages = {
    planner: view('planner'),
    analyst: view('analyst'),
    author: view('author'),
    challenger: view('challenger'),
    'sign-off': view('sign-off'),
  };
  const workingMs = RAIL.filter((stage) => stage !== 'sign-off').reduce(
    (sum, stage) => sum + stages[stage].ms,
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
