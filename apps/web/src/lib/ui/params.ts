// The advanced model parameters (chat-composer look §10, feature F74), shared by the general
// settings and the model editor. Default leaves a parameter unset so the model's or server's own
// value applies; Custom starts at a typical value. Presets other than Temperature (0.8) and
// max_tokens (128), which the spec gives, are common values (unverified against the old code).

export type ParamValue = number | string | boolean;

export interface Param {
  key: string;
  label: string;
  help: string;
  kind: 'flag' | 'number' | 'text' | 'choice';
  /** Shown to admins only. */
  admin?: boolean;
  min?: number;
  max?: number;
  step?: number;
  integer?: boolean;
  /** Where Custom starts. */
  preset?: ParamValue;
  /** For choices: the states after Default, in order. */
  options?: string[];
  placeholder?: string;
}

const number = (
  key: string,
  label: string,
  help: string,
  min: number,
  max: number,
  preset: number,
  step = 1,
  extra: Partial<Param> = {},
): Param => ({ key, label, help, kind: 'number', min, max, step, preset, ...extra });

/** In the running app's order. */
export const PARAMS: Param[] = [
  {
    key: 'stream_response',
    label: 'Stream Chat Response',
    help: 'Show the answer as it is written.',
    kind: 'flag',
  },
  number(
    'stream_delta_chunk_size',
    'Stream Delta Chunk Size',
    'How many pieces of the answer to gather before showing them.',
    1,
    128,
    1,
    1,
    { admin: true, integer: true },
  ),
  number(
    'context_compaction_threshold',
    'Context Compaction Threshold',
    'Tokens a chat may reach before earlier turns are compacted.',
    1,
    10_000_000,
    80_000,
    1,
    { admin: true, integer: true, placeholder: 'Enter token threshold' },
  ),
  {
    key: 'function_calling',
    label: 'Function Calling',
    help: 'How the model calls tools: its own way, or the prompt-based way.',
    kind: 'choice',
    options: ['native', 'legacy'],
  },
  {
    key: 'reasoning_tags',
    label: 'Reasoning Tags',
    help: 'How the model marks its reasoning in the answer.',
    kind: 'choice',
    options: ['enabled', 'disabled', 'custom'],
  },
  {
    key: 'seed',
    label: 'Seed',
    help: 'Fix the random seed so the same question gives the same answer.',
    kind: 'number',
    integer: true,
    preset: 0,
    placeholder: 'Enter Seed',
  },
  {
    key: 'stop',
    label: 'Stop Sequence',
    help: 'Text that ends the answer when the model writes it; separate several with commas.',
    kind: 'text',
    preset: '',
    placeholder: 'Enter stop sequence',
  },
  number('temperature', 'Temperature', 'Higher values give more varied answers.', 0, 2, 0.8, 0.05),
  {
    key: 'reasoning_effort',
    label: 'Reasoning Effort',
    help: 'How hard a reasoning model thinks before it answers.',
    kind: 'text',
    preset: 'medium',
    placeholder: 'Enter reasoning effort',
  },
  {
    key: 'logit_bias',
    label: 'logit_bias',
    help: 'Raise or lower the chance of given tokens.',
    kind: 'text',
    preset: '',
  },
  number('max_tokens', 'max_tokens', 'The longest an answer may be, in tokens.', -2, 131072, 128),
  number('top_k', 'top_k', 'Pick from only this many likely next words.', 0, 1000, 40, 1, {
    integer: true,
  }),
  number(
    'top_p',
    'top_p',
    'Pick from the likeliest words that add up to this share.',
    0,
    1,
    0.9,
    0.05,
  ),
  number(
    'min_p',
    'min_p',
    'Leave out words less likely than this share of the likeliest.',
    0,
    1,
    0,
    0.05,
  ),
  number(
    'frequency_penalty',
    'frequency_penalty',
    'Discourage repeating the same words.',
    -2,
    2,
    1.1,
    0.05,
  ),
  number('presence_penalty', 'presence_penalty', 'Encourage new topics.', -2, 2, 0, 0.05),
  number('mirostat', 'mirostat', 'Keep the answer surprise steady (0 off, 1 or 2 on).', 0, 2, 0),
  number('mirostat_eta', 'mirostat_eta', 'How fast the surprise target adapts.', 0, 1, 0.1, 0.05),
  number('mirostat_tau', 'mirostat_tau', 'The surprise target.', 0, 10, 5, 0.5),
  number('repeat_last_n', 'repeat_last_n', 'How far back to look for repeats.', -1, 128, 64),
  number('tfs_z', 'tfs_z', 'Cut unlikely words from the tail.', 0, 2, 1, 0.05),
  number('repeat_penalty', 'repeat_penalty', 'Discourage repeats.', -2, 2, 1.1, 0.05),
  {
    key: 'use_mmap',
    label: 'use_mmap',
    help: 'Map the model file into memory.',
    kind: 'flag',
    admin: true,
  },
  {
    key: 'use_mlock',
    label: 'use_mlock',
    help: 'Keep the model in memory.',
    kind: 'flag',
    admin: true,
  },
];

export const shownParams = (admin: boolean) => PARAMS.filter((param) => admin || !param.admin);

/** The next state when the state button is pressed: flags go default, on, off; choices step
 * through their options; numbers and text go to their preset and back to default. */
export function next(param: Param, value: ParamValue | undefined): ParamValue | undefined {
  if (param.kind === 'flag') return value === undefined ? true : value === true ? false : undefined;
  if (param.kind === 'choice') {
    const options = param.options ?? [];
    const at = value === undefined ? -1 : options.indexOf(String(value));
    return options[at + 1];
  }
  return value === undefined ? param.preset : undefined;
}

/** What the state button says. */
export function stateLabel(param: Param, value: ParamValue | undefined): string {
  if (value === undefined) return 'Default';
  if (param.kind === 'flag') return value ? 'On' : 'Off';
  if (param.kind === 'choice') {
    const text = String(value);
    return text.charAt(0).toUpperCase() + text.slice(1);
  }
  return 'Custom';
}

/** A typed value kept in range; null when it is not acceptable (Top K takes whole numbers only). */
export function setValue(param: Param, raw: string): ParamValue | null {
  if (param.kind !== 'number') return raw;
  const value = Number(raw);
  if (raw.trim() === '' || Number.isNaN(value)) return null;
  if (param.integer && !Number.isInteger(value)) return null;
  return Math.min(param.max ?? Infinity, Math.max(param.min ?? -Infinity, value));
}
