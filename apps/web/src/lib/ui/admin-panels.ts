// The admin settings panels (admin look §18 to §32), as data: each panel's sections and the rows
// and fields in them, with their starting values and the conditions that show sub-settings. One
// renderer draws them all. Left out, as the owner chose: Web Search (every engine is outside),
// cloud providers, the upstream community and licence rows. LDAP and OAuth are look-only.
import type { IconName } from '$lib/ui/icons/generated/icons';
import { version } from '../../../package.json';

export type Values = Record<string, unknown>;

export interface Item {
  kind: 'switch' | 'select' | 'text' | 'number' | 'textarea' | 'secret' | 'action' | 'info';
  label: string;
  key?: string;
  note?: string;
  placeholder?: string;
  options?: [string, string][];
  start?: unknown;
  /** Label above the control (a field) rather than beside it (a row). */
  field?: boolean;
  /** A select that fills the row. */
  wide?: boolean;
  /** A dimmer sub-setting label. */
  sub?: boolean;
  /** A word after a short number input. */
  unit?: string;
  experimental?: boolean;
  /** Shown but disabled, with this note (set up on the server). */
  locked?: string;
  /** The text button of an action row. */
  action?: string;
  /** A value shown as text (info rows). */
  value?: string;
  showIf?: (values: Values) => boolean;
}

export interface Section {
  heading?: string;
  items: Item[];
}

export interface Panel {
  id: string;
  title: string;
  sections: Section[];
  /** Panels without a Save footer act at once. */
  noSave?: boolean;
}

const on = (key: string) => (values: Values) => values[key] === true;
const sw = (
  key: string,
  label: string,
  note: string,
  start = false,
  extra: Partial<Item> = {},
): Item => ({
  kind: 'switch',
  key,
  label,
  note,
  start,
  ...extra,
});
const field = (
  kind: Item['kind'],
  key: string,
  label: string,
  note?: string,
  extra: Partial<Item> = {},
): Item => ({ kind, key, label, note, field: true, start: '', ...extra });

const SERVER = 'Configured by the server.';

export const PANELS = {
  general: {
    id: 'general',
    title: 'General',
    sections: [
      {
        items: [{ kind: 'info', label: 'Version', value: `v${version}` }],
      },
      {
        heading: 'Features',
        items: [
          sw(
            'ENABLE_MESSAGE_RATING',
            'Message Rating',
            'Let users rate assistant responses.',
            true,
          ),
          sw('ENABLE_FOLDERS', 'Folders', 'Allow users to organize chats into folders.', true),
          field(
            'number',
            'FOLDER_MAX_FILE_COUNT',
            'Folder Max File Count',
            'Maximum number of files allowed per folder.',
            {
              placeholder: 'Leave empty for unlimited',
              showIf: on('ENABLE_FOLDERS'),
            },
          ),
          sw(
            'ENABLE_MEMORIES',
            'Memories',
            'Allow users to save memories for more personalized responses.',
            true,
          ),
          sw(
            'ENABLE_MEMORY_SYSTEM_CONTEXT',
            'Memory System Context',
            'Include saved memories in the system context.',
            true,
            {
              showIf: on('ENABLE_MEMORIES'),
            },
          ),
          sw('ENABLE_NOTES', 'Notes', 'Allow users to create and manage notes.', true),
          sw(
            'ENABLE_CHANNELS',
            'Channels',
            'Allow users to use channels for shared conversations.',
          ),
          {
            kind: 'select',
            key: 'CHANNEL_RESPONSE_MODE',
            label: 'Model Response Mode',
            note: 'Choose where model responses to root-level channel mentions are posted.',
            options: [
              ['thread', 'Thread'],
              ['channel', 'Channel'],
            ],
            start: 'thread',
            showIf: on('ENABLE_CHANNELS'),
          },
          sw('ENABLE_CALENDAR', 'Calendar', 'Allow users to access calendar features.'),
          sw('ENABLE_AUTOMATIONS', 'Automations', 'Allow users to create and run automations.'),
          sw(
            'ENABLE_USER_WEBHOOKS',
            'User Webhooks',
            'Allow users to configure webhooks from their account.',
          ),
          sw('ENABLE_USER_STATUS', 'User Status', 'Show user status information in the app.', true),
          field(
            'textarea',
            'RESPONSE_WATERMARK',
            'Response Watermark',
            'Append a watermark to assistant responses when configured.',
            {
              placeholder: 'Enter a watermark for the response. Leave empty for none.',
            },
          ),
          field(
            'text',
            'WEBUI_URL',
            'WebUI URL',
            'Enter the public URL of your WebUI. This URL will be used to generate links in the notifications.',
            {
              placeholder: 'e.g.) "http://localhost:3000"',
            },
          ),
        ],
      },
    ],
  },
  authentication: {
    id: 'authentication',
    title: 'Authentication',
    sections: [
      {
        heading: 'User Access',
        items: [
          {
            kind: 'select',
            key: 'DEFAULT_USER_ROLE',
            label: 'Default User Role',
            note: 'Role assigned to new users when they create an account.',
            options: [
              ['pending', 'pending'],
              ['user', 'user'],
              ['admin', 'admin'],
            ],
            start: 'pending',
          },
          {
            kind: 'select',
            key: 'DEFAULT_GROUP_ID',
            label: 'Default Group',
            note: 'Group assigned to new users by default.',
            options: [['', 'None']],
            start: '',
          },
          sw('ENABLE_SIGNUP', 'New Sign Ups', 'Allow new users to create accounts.'),
          sw(
            'ENABLE_API_KEYS',
            'API Keys',
            'Allow users to create API keys for programmatic access.',
          ),
          sw(
            'ENABLE_API_KEYS_ENDPOINT_RESTRICTIONS',
            'API Key Endpoint Restrictions',
            'Limit API keys to configured endpoints.',
            false,
            {
              showIf: on('ENABLE_API_KEYS'),
            },
          ),
          field(
            'text',
            'API_KEYS_ALLOWED_ENDPOINTS',
            'Allowed Endpoints',
            'Comma-separated API paths that API keys can access.',
            {
              placeholder: '/api/v1/messages, /api/v1/channels',
              showIf: (values) =>
                values.ENABLE_API_KEYS === true &&
                values.ENABLE_API_KEYS_ENDPOINT_RESTRICTIONS === true,
            },
          ),
          field(
            'text',
            'JWT_EXPIRES_IN',
            'JWT Expiration',
            "Valid time units: 's', 'm', 'h', 'd', 'w' or '-1' for no expiration.",
            {
              start: '4w',
              placeholder: 'e.g.) "30m","1h", "10d".',
            },
          ),
        ],
      },
      {
        heading: 'Pending Accounts',
        items: [
          sw(
            'SHOW_ADMIN_DETAILS',
            'Admin Details',
            'Show admin contact details while an account waits for approval.',
            true,
          ),
          field(
            'text',
            'ADMIN_EMAIL',
            'Admin Contact Email',
            'Email shown in the pending account overlay.',
            {
              placeholder: 'Leave empty to use first admin user',
              showIf: on('SHOW_ADMIN_DETAILS'),
            },
          ),
          field(
            'textarea',
            'PENDING_USER_OVERLAY_TITLE',
            'Pending User Overlay Title',
            'Custom title shown while an account waits for approval.',
            {
              placeholder:
                'Enter a title for the pending user info overlay. Leave empty for default.',
            },
          ),
          field(
            'textarea',
            'PENDING_USER_OVERLAY_CONTENT',
            'Pending User Overlay Content',
            'Custom message shown while an account waits for approval.',
            {
              placeholder:
                'Enter content for the pending user info overlay. Leave empty for default.',
            },
          ),
        ],
      },
      {
        heading: 'LDAP',
        items: [
          sw('ENABLE_LDAP', 'LDAP', 'Allow users to authenticate with an LDAP directory.', false, {
            locked: SERVER,
          }),
        ],
      },
      {
        heading: 'OAuth / OIDC',
        items: [
          sw(
            'ENABLE_OAUTH',
            'OAuth / OIDC',
            'Allow users to authenticate with an OAuth / OIDC provider.',
            false,
            {
              locked: SERVER,
            },
          ),
        ],
      },
    ],
  },
  subagents: {
    id: 'subagents',
    title: 'Sub-agents',
    sections: [
      {
        items: [
          sw(
            'ENABLE_SUBAGENTS',
            'Enable sub-agents',
            'Allow the AI to delegate tasks to sub-agents. Each sub-agent creates a real chat with full tool access. Uses additional LLM calls.',
          ),
          {
            kind: 'number',
            key: 'MAX_CONCURRENT',
            label: 'Max concurrent',
            unit: 'simultaneous sub-agents',
            start: 3,
            showIf: on('ENABLE_SUBAGENTS'),
          },
          sw(
            'ENABLE_BACKGROUND',
            'Enable background sub-agents',
            'Allow delegated sub-agents to keep running while the parent chat continues.',
            false,
            {
              showIf: on('ENABLE_SUBAGENTS'),
            },
          ),
          {
            kind: 'number',
            key: 'MAX_BACKGROUND',
            label: 'Max background',
            unit: 'background sub-agents',
            start: 2,
            showIf: (values) =>
              values.ENABLE_SUBAGENTS === true && values.ENABLE_BACKGROUND === true,
          },
          {
            kind: 'number',
            key: 'MAX_ITERATIONS',
            label: 'Max iterations',
            unit: 'tool loops per sub-agent',
            start: 10,
            showIf: on('ENABLE_SUBAGENTS'),
          },
          {
            kind: 'number',
            key: 'MAX_OUTPUT',
            label: 'Max output',
            start: 4000,
            showIf: on('ENABLE_SUBAGENTS'),
          },
          field(
            'textarea',
            'SYSTEM_PROMPT',
            'System prompt',
            'Leave empty for the built-in default.',
            {
              placeholder: 'You are a sub-agent...',
              showIf: on('ENABLE_SUBAGENTS'),
            },
          ),
        ],
      },
    ],
  },
  code: {
    id: 'code',
    title: 'Code Execution',
    sections: (['Code Execution', 'Code Interpreter'] as const).map((heading) => {
      const prefix = heading === 'Code Execution' ? 'CODE_EXECUTION' : 'CODE_INTERPRETER';
      const enable =
        heading === 'Code Execution' ? 'ENABLE_CODE_EXECUTION' : 'ENABLE_CODE_INTERPRETER';
      const jupyter = (values: Values) =>
        values[enable] === true && values[`${prefix}_ENGINE`] === 'jupyter';
      return {
        heading,
        items: [
          sw(
            enable,
            `Enable ${heading}`,
            heading === 'Code Execution'
              ? 'Allow models to run generated code and return execution results.'
              : 'Allow models to use the code interpreter tool during chats.',
          ),
          {
            kind: 'select',
            key: `${prefix}_ENGINE`,
            label: `${heading} Engine`,
            options: [
              ['pyodide', 'Pyodide'],
              ['jupyter', 'Jupyter'],
            ],
            start: 'pyodide',
            showIf: on(enable),
          },
          field(
            'text',
            `${prefix}_JUPYTER_URL`,
            'Jupyter URL',
            `Connect ${heading.toLowerCase()} to a local or self-hosted Jupyter server.`,
            {
              placeholder: 'Enter Jupyter URL',
              showIf: jupyter,
            },
          ),
          {
            kind: 'select',
            key: `${prefix}_JUPYTER_AUTH`,
            label: 'Jupyter Auth',
            note: 'Select how 4CE authenticates with the Jupyter server.',
            options: [
              ['', 'None'],
              ['token', 'Token'],
              ['password', 'Password'],
            ],
            start: '',
            showIf: jupyter,
          },
          field(
            'secret',
            `${prefix}_JUPYTER_SECRET`,
            'Credentials',
            'Credentials used to authenticate with the Jupyter server.',
            {
              placeholder: 'Enter Jupyter Token',
              showIf: (values) => jupyter(values) && Boolean(values[`${prefix}_JUPYTER_AUTH`]),
            },
          ),
          field(
            'number',
            `${prefix}_TIMEOUT`,
            'Code Execution Timeout',
            'Maximum runtime in seconds before execution is stopped.',
            {
              placeholder: 'e.g. 60',
              showIf: jupyter,
            },
          ),
          ...(heading === 'Code Interpreter'
            ? [
                field(
                  'textarea',
                  'CODE_INTERPRETER_PROMPT_TEMPLATE',
                  'Code Interpreter Prompt Template',
                  'Leave empty to use the default prompt, or enter a custom prompt.',
                  {
                    showIf: on(enable),
                  },
                ),
              ]
            : []),
        ],
      };
    }),
  },
  database: {
    id: 'database',
    title: 'Database',
    noSave: true,
    sections: [
      {
        heading: 'Config',
        items: [
          {
            kind: 'action',
            key: 'import-config',
            label: 'Import Config',
            note: 'Import admin configuration from a JSON export file.',
            action: 'Import',
          },
          {
            kind: 'action',
            key: 'export-config',
            label: 'Export Config',
            note: 'Download the current admin configuration as JSON.',
            action: 'Export',
          },
        ],
      },
      {
        heading: 'Export',
        items: [
          {
            kind: 'action',
            key: 'export-database',
            label: 'Database',
            note: 'Download the application database when supported.',
            action: 'Database',
          },
          {
            kind: 'action',
            key: 'export-chats',
            label: 'All Chats',
            note: "Download every user's chat history as JSON.",
            action: 'Export',
          },
          {
            kind: 'action',
            key: 'export-users',
            label: 'Users',
            note: 'Download all users as CSV.',
            action: 'Export',
          },
        ],
      },
    ],
  },
} satisfies Record<string, Panel>;

export type PanelId = keyof typeof PANELS;

/** The admin tabs under their group captions, in the running app's order (Web Search left out). */
export const ADMIN_GROUPS: {
  caption: string;
  tabs: { id: string; label: string; icon: IconName }[];
}[] = [
  {
    caption: 'System',
    tabs: [
      { id: 'admin-general', label: 'General', icon: 'settings-general' },
      { id: 'admin-authentication', label: 'Authentication', icon: 'admin-auth' },
    ],
  },
  {
    caption: 'AI',
    tabs: [
      { id: 'admin-connections', label: 'Connections', icon: 'admin-connections' },
      { id: 'admin-models', label: 'Models', icon: 'admin-models' },
      { id: 'admin-subagents', label: 'Sub-agents', icon: 'admin-subagents' },
    ],
  },
  {
    caption: 'Experience',
    tabs: [
      { id: 'admin-interface', label: 'Interface', icon: 'admin-interface' },
      { id: 'admin-audio', label: 'Audio', icon: 'admin-audio' },
      { id: 'admin-images', label: 'Images', icon: 'admin-images' },
    ],
  },
  {
    caption: 'Quality',
    tabs: [
      { id: 'admin-evaluations', label: 'Evaluations', icon: 'admin-evaluations' },
      { id: 'admin-analytics', label: 'Analytics', icon: 'admin-analytics' },
    ],
  },
  {
    caption: 'Tools',
    tabs: [
      { id: 'admin-documents', label: 'Documents', icon: 'admin-documents' },
      { id: 'admin-code', label: 'Code Execution', icon: 'admin-code' },
      { id: 'admin-pipelines', label: 'Pipelines', icon: 'admin-pipelines' },
    ],
  },
  { caption: 'Data', tabs: [{ id: 'admin-database', label: 'Database', icon: 'admin-database' }] },
];

/** Every keyed item's starting value. */
export const panelDefaults = (panel: Panel): Values =>
  Object.fromEntries(
    panel.sections.flatMap((section) =>
      section.items
        .filter((item) => item.key && item.kind !== 'action')
        .map((item) => [item.key, item.start]),
    ),
  );

/** The section's items that show for these values. */
export const shownItems = (section: Section, values: Values) =>
  section.items.filter((item) => !item.showIf || item.showIf(values));
