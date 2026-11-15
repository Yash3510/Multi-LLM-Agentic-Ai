// What the details panel under an answer shows, worked out from the run's own record: the receipt's
// folds, the sources, the checks and the status events. Nothing here adds a fact the run did not
// record (ADR-0043 §1).
import type { Receipt, SignOffRequest, Source } from '$lib/data';
import { foldTitle } from './fold-title';

type Fold = NonNullable<Receipt['folds']>[number];

/** The fold that carries the provenance table; every other fold is an agent's own output. */
export const PROVENANCE = 'Full provenance';

export interface ProvenanceRow {
  figure: string;
  /** A citation whose source never arrived keeps its number only. */
  refs: (Source | { index: number })[];
}

/** Rows of the provenance fold's two-column markdown table. Empty when the body is not a table. */
export function provenanceRows(body: string, sources: Source[]): ProvenanceRow[] {
  const lines = body.split('\n').filter((line) => line.trim().startsWith('|'));
  return lines.slice(2).map((line) => {
    const [figure = '', cited = ''] = line
      .trim()
      .replace(/^\||\|$/g, '')
      .split('|')
      .map((cell) => cell.trim());
    const refs = [...cited.matchAll(/\[(\d+)\]/g)].map((match) => {
      const index = Number(match[1]);
      return sources.find((source) => source.index === index) ?? { index };
    });
    return { figure, refs };
  });
}

export interface ReasoningStep {
  role: string;
  step: string;
  verdict?: 'PASS' | 'FAIL';
  model?: string;
  /** The agent's output, as markdown. */
  body: string;
}

export function reasoningSteps(folds: Fold[]): ReasoningStep[] {
  return folds
    .filter((fold) => fold.title !== PROVENANCE)
    .map((fold) => {
      const { text, verdict, model } = foldTitle(fold.title);
      const [role = '', ...rest] = text.split(' · ');
      return {
        role,
        step: rest.join(' · '),
        ...(verdict ? { verdict } : {}),
        ...(model ? { model } : {}),
        body: fold.body,
      };
    });
}

export interface TimelineSpan {
  /** Offset from the run's start, as "+1.2s". */
  at: string;
  role: string;
  text: string;
  /** Where the step starts and ends on the run, from 0 to 1. */
  start: number;
  end: number;
  /** How long the step ran. Absent for the last step, which has no next step to end it. */
  took?: string;
}

const seconds = (ms: number) => `${(ms / 1000).toFixed(1)}s`;

/** Each status event as a span that runs until the next one. The run ends at its last status. */
export function timelineSpans(
  steps: { ms: number; stage: string; text: string }[],
): TimelineSpan[] {
  const total = steps.at(-1)?.ms ?? 0;
  const place = (ms: number) => (total ? ms / total : 0);
  return steps.map((step, index) => {
    const next = steps[index + 1];
    const role = step.stage.charAt(0).toUpperCase() + step.stage.slice(1);
    const prefix = `${role}: `;
    return {
      at: `+${seconds(step.ms)}`,
      role,
      text: step.text.startsWith(prefix) ? step.text.slice(prefix.length) : step.text,
      start: place(step.ms),
      end: place(next ? next.ms : step.ms),
      ...(next ? { took: seconds(next.ms - step.ms) } : {}),
    };
  });
}

export interface SourceUse extends Source {
  /** The answer's text cites it. */
  cited: boolean;
  /** The checks that rest on it. */
  supports: string[];
}

export function sourceUses(
  sources: Source[],
  checks: SignOffRequest['checks'],
  answer: string,
): SourceUse[] {
  return sources.map((source) => ({
    ...source,
    cited: answer.includes(`[${source.index}]`),
    supports: checks
      .filter((check) => check.cites?.includes(source.index))
      .map((check) => check.label),
  }));
}
