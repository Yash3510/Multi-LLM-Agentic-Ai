// Group and default permissions (admin look §12d, F74 to F82): the built-in defaults, the rows
// of the permissions tab with their nesting and conditions, and filling missing keys. The chat
// tool-settings switch maps to the running app's per-tool settings permission under its own key.

export type Category = 'workspace' | 'sharing' | 'access_grants' | 'chat' | 'features' | 'settings';
export type Permissions = Record<Category, Record<string, boolean>>;
export type StoredPermissions = Partial<Record<Category, Record<string, boolean>>>;

export const DEFAULT_PERMISSIONS: Permissions = {
  workspace: {
    models: false,
    knowledge: false,
    prompts: false,
    tools: false,
    skills: false,
    models_import: false,
    models_export: false,
    prompts_import: false,
    prompts_export: false,
    tools_import: false,
    tools_export: false,
    skills_import: false,
    skills_export: false,
  },
  sharing: {
    models: false,
    public_models: false,
    knowledge: false,
    public_knowledge: false,
    prompts: false,
    public_prompts: false,
    tools: false,
    public_tools: false,
    skills: false,
    public_skills: false,
    notes: false,
    public_notes: false,
    folders: false,
    public_chats: false,
    open_chats: false,
    public_calendars: false,
  },
  access_grants: { allow_users: true, allow_groups: true },
  chat: {
    controls: true,
    tool_settings: true,
    system_prompt: true,
    params: true,
    file_upload: true,
    web_upload: true,
    delete: true,
    delete_message: true,
    continue_response: true,
    regenerate_response: true,
    rate_response: true,
    edit: true,
    share: true,
    export: true,
    import: true,
    stt: true,
    tts: true,
    call: true,
    multiple_models: true,
    temporary: true,
    temporary_enforced: false,
  },
  features: {
    api_keys: false,
    notes: true,
    channels: true,
    folders: true,
    direct_tool_servers: false,
    web_search: true,
    image_generation: true,
    code_interpreter: true,
    memories: true,
    automations: false,
    calendar: true,
    webhooks: false,
  },
  settings: { interface: true },
};

export interface PermissionRow {
  key: string;
  label: string;
  /** Shown as a tooltip on the row. */
  warn?: string;
  /** Indented rows shown while this row is on. */
  children?: PermissionRow[];
  /** Shown only while this other switch is on. */
  showIf?: [Category, string];
}

export interface PermissionSection {
  heading: string;
  category: Category;
  rows: PermissionRow[];
}

const CODE_WARNING =
  'Warning: Enabling this will allow users to upload arbitrary code on the server.';
const row = (key: string, label: string, extra: Partial<PermissionRow> = {}): PermissionRow => ({
  key,
  label,
  ...extra,
});
const io = (thing: string, Thing: string) => [
  row(`${thing}_import`, `Import ${Thing}`),
  row(`${thing}_export`, `Export ${Thing}`),
];
const shared = (thing: string, Thing: string) => [
  row(thing, `${Thing} Sharing`),
  row(`public_${thing}`, `${Thing} Public Sharing`, { showIf: ['sharing', thing] }),
];

export const SECTIONS: PermissionSection[] = [
  {
    heading: 'Workspace Permissions',
    category: 'workspace',
    rows: [
      row('models', 'Models Access', { children: io('models', 'Models') }),
      row('knowledge', 'Knowledge Access'),
      row('prompts', 'Prompts Access', { children: io('prompts', 'Prompts') }),
      row('tools', 'Tools Access', { warn: CODE_WARNING, children: io('tools', 'Tools') }),
      row('skills', 'Skills Access', { warn: CODE_WARNING, children: io('skills', 'Skills') }),
    ],
  },
  {
    heading: 'Sharing Permissions',
    category: 'sharing',
    rows: [
      ...shared('models', 'Models'),
      ...shared('knowledge', 'Knowledge'),
      ...shared('prompts', 'Prompts'),
      ...shared('tools', 'Tools'),
      ...shared('skills', 'Skills'),
      ...shared('notes', 'Notes'),
      row('folders', 'Folders Sharing'),
      row('public_chats', 'Chats Public Sharing', { showIf: ['chat', 'share'] }),
      row('open_chats', 'Chats Open Sharing', { showIf: ['chat', 'share'] }),
      row('public_calendars', 'Calendars Public Sharing', { showIf: ['features', 'calendar'] }),
    ],
  },
  {
    heading: 'Access Grants',
    category: 'access_grants',
    rows: [
      row('allow_users', 'Allow Sharing With Users'),
      row('allow_groups', 'Allow Sharing With Groups'),
    ],
  },
  {
    heading: 'Chat Permissions',
    category: 'chat',
    rows: [
      row('file_upload', 'Allow File Upload'),
      row('web_upload', 'Allow Web Upload'),
      row('controls', 'Allow Chat Controls', {
        children: [
          row('tool_settings', 'Allow Chat Settings'),
          row('system_prompt', 'Allow Chat System Prompt'),
          row('params', 'Allow Chat Params'),
        ],
      }),
      row('edit', 'Allow Chat Edit'),
      row('delete', 'Allow Chat Delete'),
      row('delete_message', 'Allow Delete Messages'),
      row('continue_response', 'Allow Continue Response'),
      row('regenerate_response', 'Allow Regenerate Response'),
      row('rate_response', 'Allow Rate Response'),
      row('share', 'Allow Chat Share'),
      row('export', 'Allow Chat Export'),
      row('import', 'Allow Chat Import'),
      row('stt', 'Allow Speech to Text'),
      row('tts', 'Allow Text to Speech'),
      row('call', 'Allow Call'),
      row('multiple_models', 'Allow Multiple Models in Chat'),
      row('temporary', 'Allow Temporary Chat', {
        children: [row('temporary_enforced', 'Enforce Temporary Chat')],
      }),
    ],
  },
  {
    heading: 'Features Permissions',
    category: 'features',
    rows: [
      row('api_keys', 'API Keys'),
      row('notes', 'Notes'),
      row('channels', 'Channels'),
      row('folders', 'Folders'),
      row('direct_tool_servers', 'Direct Tool Servers'),
      row('web_search', 'Web Search'),
      row('image_generation', 'Image Generation'),
      row('code_interpreter', 'Code Interpreter'),
      row('memories', 'Memories'),
      row('automations', 'Automations', {
        warn: 'Enabling this lets users run scheduled prompts automatically.',
      }),
      row('calendar', 'Calendar'),
      row('webhooks', 'User Webhooks'),
    ],
  },
  {
    heading: 'Settings Permissions',
    category: 'settings',
    rows: [row('interface', 'Interface Settings Access')],
  },
];

const CATEGORIES = Object.keys(DEFAULT_PERMISSIONS) as Category[];

/** Stored values over the built-in defaults, category by category. */
export function fillPermissions(stored: StoredPermissions): Permissions {
  return Object.fromEntries(
    CATEGORIES.map((category) => [
      category,
      { ...DEFAULT_PERMISSIONS[category], ...stored[category] },
    ]),
  ) as Permissions;
}

/** The section's rows that show for these permissions. */
export const visibleRows = (section: PermissionSection, permissions: Permissions) =>
  section.rows.filter((one) => !one.showIf || permissions[one.showIf[0]][one.showIf[1]]);

/** Whether a group stores any permission of its own. */
export const hasCustom = (stored: StoredPermissions) =>
  Object.values(stored).some((values) => values && Object.keys(values).length > 0);
