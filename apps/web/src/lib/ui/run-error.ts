// What a stopped run's error means, in plain words (own-4ce features F28): the cause matched by
// phrase in the advice or the server's detail, with its icon, title, subline, steps and command.
import type { IconName } from '$lib/ui/icons/generated/icons';

export type RunErrorCause = 'server' | 'model' | 'long' | 'slow' | 'unknown';

export interface RunErrorView {
  cause: RunErrorCause;
  icon: IconName;
  title: string;
  subline: string;
  steps: string[];
  command?: string;
}

const FIX = 'python 4ce/preflight.py --fix';

const MATCH: [RunErrorCause, RegExp][] = [
  [
    'server',
    /unreachable|connection refused|cannot connect|connection attempts failed|connect error/i,
  ],
  ['model', /not loaded|model not found|not found|no model|does not exist/i],
  [
    'long',
    /context window|exceeds the available context|context (size|length)|maximum context|too many tokens/i,
  ],
  ['slow', /took too long|timed out|timeout/i],
];

export function explainRunError({
  detail,
  advice,
  role = '4CE',
}: {
  detail: string;
  advice?: string;
  role?: string;
}): RunErrorView {
  const text = `${advice ?? ''}\n${detail}`;
  const cause = MATCH.find(([, pattern]) => pattern.test(text))?.[0] ?? 'unknown';
  switch (cause) {
    case 'server':
      return {
        cause,
        icon: 'plugs',
        title: "The model server isn't running",
        subline: `${role} could not reach the local models.`,
        steps: [
          'Open Bionic.',
          'Turn on its server: Developer, then Start Server.',
          'Then try again.',
        ],
      };
    case 'model': {
      const model = /["“']([^"”']+)["”']/.exec(detail)?.[1];
      return {
        cause,
        icon: 'cube',
        title: "A model isn't loaded",
        subline: model
          ? `${role} was routed to ${model}, which Bionic has not loaded.`
          : `${role} was routed to a model Bionic has not loaded.`,
        steps: ["Load 4CE's models in Bionic, or run the command below.", 'Then try again.'],
        command: FIX,
      };
    }
    case 'long':
      return {
        cause,
        icon: 'file-text',
        title: 'This request is too long for the model',
        subline: "It is longer than the model's context window.",
        steps: [
          'Attach long documents instead of pasting them, so only the passages that matter are sent.',
          'Then try again.',
        ],
      };
    case 'slow':
      return {
        cause,
        icon: 'clock',
        title: 'The model took too long to answer',
        subline: `${role} waited, then stopped.`,
        steps: [
          'If answers are slow in general, a model is probably loaded above 8192 context. Run the command below.',
          'Then try again.',
        ],
        command: FIX,
      };
    default:
      return {
        cause,
        icon: 'warning-circle',
        title: 'The run stopped',
        subline: `Something went wrong while ${role} was working.`,
        steps: [advice ?? 'Try again. If it happens again, what the model server said is below.'],
      };
  }
}
