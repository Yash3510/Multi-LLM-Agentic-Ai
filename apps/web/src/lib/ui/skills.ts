// Skill rules (workspace F104, F105): the id made from the name, front matter, and importing a
// Markdown or JSON file.

export interface SkillDraft {
  id: string;
  name: string;
  description: string;
  instructions: string;
}

/** Accents stripped, spaces to hyphens, only letters, digits, - and _ kept, lowercased. */
export const skillId = (name: string) =>
  name
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^a-zA-Z0-9_-]/g, '')
    .toLowerCase();

/** Simple "key: value" lines between two lines of three dashes at the very top. */
export function frontmatter(text: string): Record<string, string> {
  const block = /^---\n([\s\S]*?)\n---/.exec(text);
  if (!block) return {};
  return Object.fromEntries(
    block[1]
      .split('\n')
      .map((line) => /^([\w-]+):\s*(.*)$/.exec(line))
      .filter((match): match is RegExpExecArray => match !== null)
      .map(([, key, value]) => [key, value.replace(/^["']|["']$/g, '')]),
  );
}

/** Hyphens and underscores to spaces, each word capitalised. */
export const titleCase = (text: string) =>
  text.replace(/[-_]+/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());

/** A JSON list or object as it is, or a Markdown file named from its front matter or file. */
export function readSkillFile(fileName: string, text: string): SkillDraft[] {
  if (fileName.toLowerCase().endsWith('.json')) {
    const parsed: unknown = JSON.parse(text);
    return (Array.isArray(parsed) ? parsed : [parsed]) as SkillDraft[];
  }
  const meta = frontmatter(text);
  const base = meta.name ?? fileName.replace(/\.[^.]+$/, '');
  return [
    {
      id: skillId(base.replace(/_/g, '-')),
      name: titleCase(base),
      description: meta.description ?? '',
      instructions: text,
    },
  ];
}

/** Saves skills as a JSON file named with the time (F100, F103). */
export function saveSkillFile(skills: object[], name = 'skills-export') {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(skills, null, 2)], { type: 'application/json' }),
  );
  Object.assign(document.createElement('a'), {
    href: url,
    download: `${name}-${Date.now()}.json`,
  }).click();
  URL.revokeObjectURL(url);
}
