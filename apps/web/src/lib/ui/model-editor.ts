// The model editor's rules (workspace features F35 to F54), apart from its look: the id made from
// the name, what each checklist offers, the type-ahead search, and the record that is saved.

export const CAPABILITIES = [
  ['vision', 'Vision'],
  ['file_upload', 'File Upload'],
  ['file_context', 'File Context'],
  ['web_search', 'Web Search'],
  ['image_generation', 'Image Generation'],
  ['code_interpreter', 'Code Interpreter'],
  ['terminal', 'Terminal'],
  ['usage', 'Usage'],
  ['citations', 'Citations'],
  ['status_updates', 'Status Updates'],
  ['memory', 'Memory'],
  ['builtin_tools', 'Builtin Tools'],
] as const;

export const BUILTIN_TOOLS = [
  ['time', 'Time & Calculation'],
  ['ask_user', 'Ask User'],
  ['memory', 'Memory'],
  ['chat_history', 'Chat History'],
  ['notes', 'Notes'],
  ['knowledge', 'Knowledge Base'],
  ['files', 'Files'],
  ['channels', 'Channels'],
  ['notifications', 'Notifications'],
  ['web_search', 'Web Search'],
  ['image_generation', 'Image Generation'],
  ['code_interpreter', 'Code Interpreter'],
  ['tasks', 'Task Management'],
  ['automations', 'Automations'],
  ['calendar', 'Calendar'],
  ['subagents', 'Sub-agents'],
] as const;

export type Capability = (typeof CAPABILITIES)[number][0];
export type BuiltinTool = (typeof BUILTIN_TOOLS)[number][0];
/** The capabilities that can start switched on in a new chat (F47). */
const FEATURES = ['web_search', 'image_generation', 'code_interpreter'] as const;
export type Feature = (typeof FEATURES)[number];

export const label = (key: string) =>
  [...CAPABILITIES, ...BUILTIN_TOOLS].find(([id]) => id === key)?.[1] ?? key;

export interface Suggestion {
  title: [string, string];
  content: string;
}

export interface ModelDraft {
  id: string;
  name: string;
  base: string;
  description: { custom: boolean; text: string };
  tags: string[];
  system: string;
  suggestions: Suggestion[] | null;
  knowledge: { id: string; name: string }[];
  tools: string[];
  skills: string[];
  capabilities: Record<Capability, boolean>;
  defaultFeatures: Feature[];
  builtinTools: Record<BuiltinTool, boolean>;
}

/** A new model: every capability on except Usage, every builtin tool on (F46, F48). */
export const blankDraft = (): ModelDraft => ({
  id: '',
  name: '',
  base: '',
  // A new model opens with an empty custom description, as the running app does.
  description: { custom: true, text: '' },
  tags: [],
  system: '',
  suggestions: null,
  knowledge: [],
  tools: [],
  skills: [],
  capabilities: Object.fromEntries(CAPABILITIES.map(([id]) => [id, id !== 'usage'])) as Record<
    Capability,
    boolean
  >,
  defaultFeatures: [],
  builtinTools: Object.fromEntries(BUILTIN_TOOLS.map(([id]) => [id, true])) as Record<
    BuiltinTool,
    boolean
  >,
});

/** The id made live from the name while creating (F35). */
export const modelId = (name: string) =>
  name
    .replace(/\s+/g, '-')
    .replace(/[^a-zA-Z0-9-]/g, '')
    .toLowerCase();

/** The first thing missing, in the order the running app checks (F51). */
export function validate(draft: ModelDraft): string | undefined {
  if (!draft.id.trim()) return 'Model ID is required.';
  if (!draft.name.trim()) return 'Model Name is required.';
  if (!draft.base) return 'Base Model is required.';
  return undefined;
}

/** File Context only shows while File Upload is on (F46). */
export const shownCapabilities = (caps: Record<Capability, boolean>): Capability[] =>
  CAPABILITIES.map(([id]) => id).filter((id) => id !== 'file_context' || caps.file_upload);

export const defaultFeatureChoices = (caps: Record<Capability, boolean>): Feature[] =>
  FEATURES.filter((id) => caps[id]);

/** Items whose id, name or description holds the search, ignoring case (F54). */
export function matching<T extends { id: string; name: string; description?: string }>(
  items: T[],
  query: string,
): T[] {
  const q = query.trim().toLowerCase();
  return items.filter((item) =>
    [item.id, item.name, item.description ?? ''].some((text) => text.toLowerCase().includes(q)),
  );
}

export interface SavedModel {
  id: string;
  name: string;
  base: string;
  params: { system?: string };
  meta: {
    description: string | null;
    tags?: { name: string }[];
    suggestionPrompts?: Suggestion[];
    knowledge?: { id: string; name: string }[];
    toolIds?: string[];
    skillIds?: string[];
    capabilities: Record<Capability, boolean>;
    defaultFeatures?: Feature[];
    builtinTools?: Partial<Record<BuiltinTool, false>>;
  };
}

/** The record to save: empty values are left out rather than saved empty (F51). */
export function payload(draft: ModelDraft, mode: 'create' | 'edit'): SavedModel {
  const text = draft.description.text.trim();
  const system = draft.system.trim();
  const off = BUILTIN_TOOLS.map(([id]) => id).filter((id) => !draft.builtinTools[id]);
  const features = draft.defaultFeatures.filter((id) => draft.capabilities[id]);
  // Creating drops suggestions with no content; editing keeps them as typed, as the app does.
  const suggestions =
    mode === 'create'
      ? draft.suggestions?.filter((item) => item.content.trim())
      : draft.suggestions;
  return {
    id: draft.id,
    name: draft.name,
    base: draft.base,
    params: system ? { system: draft.system } : {},
    meta: {
      description: draft.description.custom && text ? draft.description.text : null,
      ...(draft.tags.length && { tags: draft.tags.map((name) => ({ name })) }),
      ...(suggestions?.length && { suggestionPrompts: suggestions }),
      ...(draft.knowledge.length && { knowledge: draft.knowledge }),
      ...(draft.tools.length && { toolIds: draft.tools }),
      ...(draft.skills.length && { skillIds: draft.skills }),
      capabilities: draft.capabilities,
      ...(features.length && { defaultFeatures: features }),
      ...(off.length && {
        builtinTools: Object.fromEntries(off.map((id) => [id, false])) as Partial<
          Record<BuiltinTool, false>
        >,
      }),
    },
  };
}
