// Prompt rules (workspace F92, F93): the command made from the name, what a command may hold, and
// the draft a clone starts from.

/** Lowercase words joined by hyphens. */
export const commandFrom = (name: string) =>
  name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');

/** Letters, digits, hyphens and underscores; the message names only the first three, as the app
 * does. */
export const isCommand = (command: string) => /^[a-zA-Z0-9_-]+$/.test(command);

export const COMMAND_RULE =
  'Only alphanumeric characters and hyphens are allowed in the command string.';

export interface PromptDraft {
  name: string;
  command: string;
  content: string;
  tags: string[];
}

export const cloneDraft = (from: PromptDraft): PromptDraft => ({
  name: `${from.name} (Clone)`,
  command: commandFrom(`${from.command} clone`),
  content: from.content,
  tags: [...from.tags],
});

/** An imported JSON file's prompts: only command, name and content are kept (F92). A leading
 * slash on an older command is dropped. */
export function readPromptFile(json: string): PromptDraft[] {
  const parsed: unknown = JSON.parse(json);
  if (!Array.isArray(parsed)) throw new Error('The file must hold a list of prompts.');
  return parsed.map((entry: Record<string, unknown>) => ({
    command: String(entry.command ?? '').replace(/^\//, ''),
    name: String(entry.name ?? entry.title ?? ''),
    content: String(entry.content ?? ''),
    tags: [],
  }));
}

/** Saves prompts as a JSON file named with the time, as the running app does (F88). */
export function savePromptFile(prompts: object[]) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(prompts, null, 2)], { type: 'application/json' }),
  );
  const link = Object.assign(document.createElement('a'), {
    href: url,
    download: `prompts-export-${Date.now()}.json`,
  });
  link.click();
  URL.revokeObjectURL(url);
}
