// The admin settings panels (admin look §18 to §32), as data: each panel's sections and the rows
// and fields in them, with their starting values and the conditions that show sub-settings. One
// renderer draws them all. Left out, as the owner chose: Web Search (every engine is outside),
// cloud providers, the upstream community and licence rows. LDAP and OAuth are look-only.
import type { IconName } from '$lib/ui/icons/generated/icons';
import { version } from '../../../package.json';

export type Values = Record<string, unknown>;

export interface Item {
  kind:
    'switch' | 'select' | 'text' | 'number' | 'textarea' | 'secret' | 'action' | 'info' | 'params';
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
  /** Half the row, beside its neighbour (from 640 px). */
  half?: boolean;
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

const DEFAULT_PROMPT = 'Leave empty to use the default prompt, or enter a custom prompt';
const notBypassed = (values: Values) => values.BYPASS_EMBEDDING_AND_RETRIEVAL !== true;
const retrieving = (values: Values) => notBypassed(values) && values.RAG_FULL_CONTEXT !== true;
const hybrid = (values: Values) => retrieving(values) && values.ENABLE_RAG_HYBRID_SEARCH === true;
/** A generation switch and the prompt it reveals. */
const generation = (
  key: string,
  label: string,
  note: string,
  prompt: string,
  promptNote: string,
): Item[] => [
  sw(`ENABLE_${key}_GENERATION`, label, note, true),
  field('textarea', `${key}_GENERATION_PROMPT_TEMPLATE`, prompt, promptNote, {
    placeholder: DEFAULT_PROMPT,
    showIf: on(`ENABLE_${key}_GENERATION`),
  }),
];

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
  interface: {
    id: 'interface',
    title: 'Interface',
    sections: [
      {
        heading: 'Tasks',
        items: [
          {
            kind: 'info',
            label: 'Task Model',
            value: '',
            note: 'Choose fallback models for background tasks. Current Model follows the active chat model.',
          },
          field('select', 'TASK_MODEL', 'Local Task Model', undefined, {
            options: [['', 'Current Model']],
            half: true,
            wide: true,
          }),
          field('select', 'TASK_MODEL_EXTERNAL', 'External Task Model', undefined, {
            options: [['', 'Current Model']],
            half: true,
            wide: true,
          }),
          { kind: 'params', key: 'TASK_MODEL_PARAMS', label: 'Task Model Parameters', start: {} },
        ],
      },
      {
        heading: 'Chat',
        items: [
          sw(
            'ENABLE_TOOL_PERMISSIONS',
            'Tool Permissions',
            'Show Full access and Ask for approval in the chat input menu.',
            false,
            { experimental: true },
          ),
          sw(
            'ENABLE_CONTEXT_COMPACTION',
            'Context Compaction',
            'Summarize older chat history when the conversation context grows large.',
          ),
          field(
            'select',
            'CONTEXT_COMPACTION_MODEL',
            'Context Compaction Model',
            'Choose a dedicated model for context compaction summaries. Current Model follows the active chat model.',
            {
              options: [['', 'Current Model']],
              wide: true,
              showIf: on('ENABLE_CONTEXT_COMPACTION'),
            },
          ),
          field(
            'number',
            'CONTEXT_COMPACTION_THRESHOLD',
            'Token Threshold',
            'Older messages are summarized when estimated context exceeds this token limit.',
            { start: 80000, showIf: on('ENABLE_CONTEXT_COMPACTION') },
          ),
          field(
            'number',
            'CONTEXT_COMPACTION_CAP',
            'Token Cap',
            'Model-specific context compaction thresholds cannot exceed this token limit.',
            { start: 200000, showIf: on('ENABLE_CONTEXT_COMPACTION') },
          ),
          field(
            'number',
            'CONTEXT_COMPACTION_RETAINED',
            'Retained Messages',
            'Percentage of recent messages to keep after older messages are summarized.',
            { start: 30, showIf: on('ENABLE_CONTEXT_COMPACTION') },
          ),
          field(
            'textarea',
            'CONTEXT_COMPACTION_PROMPT',
            'Context Compaction Prompt',
            'Controls how older messages are rewritten into a running summary.',
            { placeholder: DEFAULT_PROMPT, showIf: on('ENABLE_CONTEXT_COMPACTION') },
          ),
        ],
      },
      {
        heading: 'Generation',
        items: [
          ...generation(
            'TITLE',
            'Title Generation',
            'Allow automatic names for new chats.',
            'Title Generation Prompt',
            'Shapes the short label generated for each chat.',
          ),
          ...generation(
            'VOICE_MODE_PROMPT',
            'Voice Mode Prompt',
            'Apply voice-specific instructions while voice mode is active.',
            'Prompt Template',
            'Defines the behavior used for spoken conversations.',
          ),
          ...generation(
            'FOLLOW_UP',
            'Follow Up Generation',
            'Show suggested next questions after assistant responses.',
            'Follow Up Generation Prompt',
            'Guides the suggestions shown after an assistant response.',
          ),
          ...generation(
            'TAGS',
            'Tags Generation',
            'Create chat tags from conversation content.',
            'Tags Generation Prompt',
            'Controls how chat tags are inferred.',
          ),
          sw(
            'ENABLE_RETRIEVAL_QUERY_GENERATION',
            'Retrieval Query Generation',
            'Rewrite user requests for knowledge retrieval.',
            true,
          ),
          field(
            'textarea',
            'QUERY_GENERATION_PROMPT',
            'Query Generation Prompt',
            'Shared prompt for retrieval query rewriting.',
            { placeholder: DEFAULT_PROMPT },
          ),
          sw(
            'ENABLE_AUTOCOMPLETE_GENERATION',
            'Autocomplete Generation',
            'Suggest completions while users type chat messages.',
          ),
          field(
            'number',
            'AUTOCOMPLETE_INPUT_MAX_LENGTH',
            'Autocomplete Generation Input Max Length',
            'Limit how much draft text is sent for suggestion generation.',
            {
              placeholder: '-1 for no limit, or a positive integer for a specific limit',
              showIf: on('ENABLE_AUTOCOMPLETE_GENERATION'),
            },
          ),
          field(
            'textarea',
            'AUTOCOMPLETE_PROMPT',
            'Autocomplete Generation Prompt',
            'Guides inline completions while users type a message.',
            { placeholder: DEFAULT_PROMPT, showIf: on('ENABLE_AUTOCOMPLETE_GENERATION') },
          ),
          field(
            'textarea',
            'IMAGE_PROMPT_GENERATION_PROMPT',
            'Image Prompt Generation Prompt',
            'Rewrites user intent into an image-generation prompt.',
            { placeholder: DEFAULT_PROMPT },
          ),
          field(
            'textarea',
            'TOOLS_FUNCTION_CALLING_PROMPT',
            'Tools Function Calling Prompt',
            'Guides how the assistant formats tool and function calls.',
            { placeholder: DEFAULT_PROMPT },
          ),
        ],
      },
    ],
  },
  audio: {
    id: 'audio',
    title: 'Audio',
    sections: [
      {
        heading: 'Speech-to-Text',
        items: [
          {
            kind: 'select',
            key: 'STT_ENGINE',
            label: 'Speech-to-Text Engine',
            note: 'Choose the transcription provider used for audio input.',
            options: [['', 'Whisper (Local)']],
            start: '',
          },
          field(
            'text',
            'STT_SUPPORTED_CONTENT_TYPES',
            'Supported MIME Types',
            'Comma-separated audio or video MIME types accepted for upload.',
            { placeholder: 'e.g., audio/wav,audio/mpeg,video/* (leave blank for defaults)' },
          ),
          field('text', 'WHISPER_MODEL', 'STT Model', '4CE uses faster-whisper internally.', {
            start: 'base',
            placeholder: 'Set whisper model',
          }),
        ],
      },
      {
        heading: 'Text-to-Speech',
        items: [
          {
            kind: 'select',
            key: 'TTS_ENGINE',
            label: 'Text-to-Speech Engine',
            note: 'Choose the speech provider used for assistant audio output.',
            options: [
              ['', 'Web API'],
              ['transformers', 'Transformers (Local)'],
            ],
            start: '',
          },
          field('select', 'TTS_VOICE', 'TTS Voice', undefined, {
            options: [['', 'Default']],
            wide: true,
            showIf: (values) => values.TTS_ENGINE === '',
          }),
          field(
            'text',
            'TTS_MODEL',
            'TTS Model',
            '4CE uses SpeechT5 and CMU Arctic speaker embeddings.',
            {
              placeholder: 'CMU ARCTIC speaker embedding name',
              showIf: (values) => values.TTS_ENGINE === 'transformers',
            },
          ),
          {
            kind: 'select',
            key: 'TTS_SPLIT_ON',
            label: 'Response Splitting',
            note: "Control how message text is split for TTS requests. 'Punctuation' splits into sentences, 'paragraphs' splits into paragraphs, and 'none' keeps the message as a single string.",
            options: [
              ['punctuation', 'Punctuation'],
              ['paragraphs', 'Paragraphs'],
              ['none', 'None'],
            ],
            start: 'punctuation',
          },
        ],
      },
    ],
  },
  images: {
    id: 'images',
    title: 'Images',
    sections: [
      {
        items: [
          sw(
            'ENABLE_IMAGE_GENERATION',
            'Image Generation',
            'Allow users to generate images from prompts.',
          ),
        ],
      },
      {
        heading: 'Create Image',
        items: [
          {
            kind: 'select',
            key: 'IMAGE_GENERATION_ENGINE',
            label: 'Image Generation Engine',
            note: 'Choose the provider used for image generation.',
            options: [
              ['comfyui', 'ComfyUI'],
              ['automatic1111', 'Automatic1111'],
            ],
            start: 'comfyui',
          },
          field('text', 'IMAGE_GENERATION_MODEL', 'Model', undefined, {
            placeholder: 'Select a model',
            showIf: on('ENABLE_IMAGE_GENERATION'),
          }),
          field('text', 'IMAGE_SIZE', 'Image Size', undefined, {
            placeholder: 'Enter Image Size (e.g. 512x512)',
            start: '512x512',
            showIf: on('ENABLE_IMAGE_GENERATION'),
          }),
          field('number', 'IMAGE_STEPS', 'Steps', undefined, {
            placeholder: 'Enter Number of Steps (e.g. 50)',
            start: 50,
            showIf: on('ENABLE_IMAGE_GENERATION'),
          }),
          sw(
            'ENABLE_IMAGE_PROMPT_GENERATION',
            'Image Prompt Generation',
            'Generate an image prompt before sending the request.',
            true,
            { showIf: on('ENABLE_IMAGE_GENERATION') },
          ),
          field(
            'text',
            'COMFYUI_BASE_URL',
            'Base URL',
            'Connect to the ComfyUI server used for generation.',
            {
              placeholder: 'Enter URL (e.g. http://127.0.0.1:8188/)',
              showIf: (values) => values.IMAGE_GENERATION_ENGINE === 'comfyui',
            },
          ),
          field(
            'secret',
            'COMFYUI_API_KEY',
            'API Key',
            'Use an API key when your ComfyUI server requires one.',
            {
              placeholder: 'sk-1234',
              showIf: (values) => values.IMAGE_GENERATION_ENGINE === 'comfyui',
            },
          ),
          field(
            'text',
            'AUTOMATIC1111_BASE_URL',
            'Base URL',
            'Connect to a stable-diffusion-webui server running with the `--api` flag.',
            {
              placeholder: 'Enter URL (e.g. http://127.0.0.1:7860/)',
              showIf: (values) => values.IMAGE_GENERATION_ENGINE === 'automatic1111',
            },
          ),
          field(
            'secret',
            'AUTOMATIC1111_API_AUTH',
            'API Auth String',
            'Provide the --api-auth username and password when required.',
            {
              placeholder: 'Enter api auth string (e.g. username:password)',
              showIf: (values) => values.IMAGE_GENERATION_ENGINE === 'automatic1111',
            },
          ),
          field(
            'textarea',
            'AUTOMATIC1111_PARAMS',
            'Additional Parameters',
            'Send extra JSON parameters with each AUTOMATIC1111 request.',
            {
              start: '{}',
              placeholder: 'Enter additional parameters in JSON format',
              showIf: (values) => values.IMAGE_GENERATION_ENGINE === 'automatic1111',
            },
          ),
        ],
      },
      {
        heading: 'Edit Image',
        items: [
          sw('ENABLE_IMAGE_EDIT', 'Image Edit', 'Allow users to edit existing images.'),
          {
            kind: 'select',
            key: 'IMAGE_EDIT_ENGINE',
            label: 'Image Edit Engine',
            note: 'Choose the provider used for image edits.',
            options: [['comfyui', 'ComfyUI']],
            start: 'comfyui',
          },
          field(
            'text',
            'IMAGES_EDIT_COMFYUI_BASE_URL',
            'Base URL',
            'Connect to the ComfyUI server used for image edits.',
            { placeholder: 'Enter URL (e.g. http://127.0.0.1:8188/)' },
          ),
          field(
            'secret',
            'IMAGES_EDIT_COMFYUI_API_KEY',
            'API Key',
            'Use an API key when your ComfyUI server requires one.',
            { placeholder: 'sk-1234' },
          ),
        ],
      },
    ],
  },
  documents: {
    id: 'documents',
    title: 'Documents',
    sections: [
      {
        heading: 'Content Extraction',
        items: [
          {
            kind: 'select',
            key: 'CONTENT_EXTRACTION_ENGINE',
            label: 'Content Extraction Engine',
            note: 'Choose how uploaded documents are parsed before indexing.',
            options: [
              ['', 'Default'],
              ['tika', 'Tika'],
              ['docling', 'Docling'],
              ['mineru', 'MinerU'],
            ],
            start: '',
          },
          field(
            'text',
            'MEDIA_MIME_TYPES',
            'Supported Media MIME Types',
            'Media upload MIME types the content extraction engine may process.',
            { placeholder: 'image/*, video/*' },
          ),
          sw(
            'PDF_EXTRACT_IMAGES',
            'PDF Extract Images (OCR)',
            'Extract images from PDFs so OCR can process image-only pages.',
            false,
            { showIf: (values) => values.CONTENT_EXTRACTION_ENGINE === '' },
          ),
          {
            kind: 'select',
            key: 'PDF_LOADER_MODE',
            label: 'PDF Loader Mode',
            note: 'Page mode creates one document per page. Single mode keeps pages together for chunking across boundaries.',
            options: [
              ['page', 'Page'],
              ['single', 'Single'],
            ],
            start: 'page',
            showIf: (values) => values.CONTENT_EXTRACTION_ENGINE === '',
          },
          field(
            'text',
            'TIKA_SERVER_URL',
            'Tika Server URL',
            'Tika server endpoint used for content extraction.',
            {
              placeholder: 'Enter Tika Server URL',
              showIf: (values) => values.CONTENT_EXTRACTION_ENGINE === 'tika',
            },
          ),
          {
            kind: 'select',
            key: 'TIKA_SERVER_VERSION',
            label: 'Tika Server Version',
            note: 'Select the Tika server API version.',
            options: [
              ['3', 'Tika 3.x'],
              ['4', 'Tika 4.x'],
            ],
            start: '3',
            showIf: (values) => values.CONTENT_EXTRACTION_ENGINE === 'tika',
          },
          field(
            'text',
            'DOCLING_SERVER_URL',
            'Docling Server URL',
            'Docling service endpoint used for parsing.',
            {
              placeholder: 'Enter Docling Server URL',
              showIf: (values) => values.CONTENT_EXTRACTION_ENGINE === 'docling',
            },
          ),
          field('secret', 'DOCLING_API_KEY', 'API Key', 'API key sent to Docling.', {
            placeholder: 'Enter Docling API Key',
            showIf: (values) => values.CONTENT_EXTRACTION_ENGINE === 'docling',
          }),
          field(
            'textarea',
            'DOCLING_PARAMS',
            'Parameters',
            'Additional Docling parameters in JSON format.',
            {
              placeholder: 'Enter additional parameters in JSON format',
              showIf: (values) => values.CONTENT_EXTRACTION_ENGINE === 'docling',
            },
          ),
          field(
            'text',
            'MINERU_API_URL',
            'API URL',
            'MinerU API endpoint for the local API mode.',
            { showIf: (values) => values.CONTENT_EXTRACTION_ENGINE === 'mineru' },
          ),
          field(
            'number',
            'MINERU_API_TIMEOUT',
            'API Timeout',
            'Maximum time in seconds to wait for MinerU API responses.',
            {
              placeholder: '60',
              showIf: (values) => values.CONTENT_EXTRACTION_ENGINE === 'mineru',
            },
          ),
          field(
            'text',
            'MINERU_FILE_EXTENSIONS',
            'File Extensions',
            'Comma-separated extensions MinerU should handle.',
            {
              placeholder: 'pdf, docx, pptx, xlsx',
              showIf: (values) => values.CONTENT_EXTRACTION_ENGINE === 'mineru',
            },
          ),
          sw(
            'BYPASS_EMBEDDING_AND_RETRIEVAL',
            'Bypass Embedding and Retrieval',
            'Use segmented retrieval for focused and relevant context.',
          ),
          {
            kind: 'select',
            key: 'TEXT_SPLITTER',
            label: 'Text Splitter',
            note: 'Choose how extracted text is split before indexing.',
            options: [
              ['', 'Default (Character)'],
              ['token', 'Token (Tiktoken)'],
              ['token_transformers', 'Token (Transformers)'],
            ],
            start: '',
            showIf: notBypassed,
          },
          field(
            'text',
            'TOKENIZER_MODEL',
            'Tokenizer Model',
            'Tokenizer model used for transformer token splitting.',
            {
              placeholder: 'Enter Tokenizer Model',
              showIf: (values) =>
                notBypassed(values) && values.TEXT_SPLITTER === 'token_transformers',
            },
          ),
          sw(
            'ENABLE_MARKDOWN_HEADER_TEXT_SPLITTER',
            'Markdown Header Text Splitter',
            'Split documents by markdown headers before character or token splitting.',
            true,
            { showIf: notBypassed },
          ),
          field('number', 'CHUNK_SIZE', 'Chunk Size', 'Maximum size for each text chunk.', {
            start: 1000,
            placeholder: 'Enter Chunk Size',
            half: true,
            showIf: notBypassed,
          }),
          field(
            'number',
            'CHUNK_OVERLAP',
            'Chunk Overlap',
            'Overlap preserved between neighboring chunks.',
            { start: 100, placeholder: 'Enter Chunk Overlap', half: true, showIf: notBypassed },
          ),
          field(
            'number',
            'CHUNK_MIN_SIZE_TARGET',
            'Chunk Min Size Target',
            'Merge chunks smaller than this threshold when possible. Set to 0 to disable merging.',
            {
              start: 0,
              placeholder: 'Enter Chunk Min Size Target',
              showIf: (values) =>
                notBypassed(values) && values.ENABLE_MARKDOWN_HEADER_TEXT_SPLITTER === true,
            },
          ),
        ],
      },
      {
        heading: 'Embedding',
        items: [
          {
            kind: 'select',
            key: 'RAG_EMBEDDING_ENGINE',
            label: 'Embedding Model Engine',
            note: 'Provider used to generate document embeddings.',
            options: [
              ['', 'Default (SentenceTransformers)'],
              ['ollama', 'Ollama'],
            ],
            start: '',
            showIf: notBypassed,
          },
          field(
            'text',
            'RAG_OLLAMA_BASE_URL',
            'API Base URL',
            'Ollama endpoint used for embeddings.',
            {
              placeholder: 'http://localhost:11434',
              showIf: (values) => notBypassed(values) && values.RAG_EMBEDDING_ENGINE === 'ollama',
            },
          ),
          field(
            'secret',
            'RAG_OLLAMA_API_KEY',
            'API Key',
            'Optional API key for Ollama requests.',
            { showIf: (values) => notBypassed(values) && values.RAG_EMBEDDING_ENGINE === 'ollama' },
          ),
          field(
            'text',
            'RAG_EMBEDDING_MODEL',
            'Embedding Model',
            'Model used to generate embeddings. Reindex knowledge after changing this.',
            { start: 'sentence-transformers/all-MiniLM-L6-v2', showIf: notBypassed },
          ),
          {
            kind: 'number',
            key: 'RAG_EMBEDDING_BATCH_SIZE',
            label: 'Embedding Batch Size',
            note: 'Number of items processed per embedding batch.',
            start: 1,
            showIf: notBypassed,
          },
          sw(
            'ENABLE_ASYNC_EMBEDDING',
            'Async Embedding Processing',
            'Run embedding tasks concurrently to speed up processing.',
            true,
            { showIf: notBypassed },
          ),
          {
            kind: 'number',
            key: 'RAG_EMBEDDING_CONCURRENT_REQUESTS',
            label: 'Embedding Concurrent Requests',
            note: 'Maximum concurrent embedding requests. Set to 0 for unlimited.',
            start: 0,
            showIf: notBypassed,
          },
        ],
      },
      {
        heading: 'Retrieval',
        items: [
          sw(
            'RAG_FULL_CONTEXT',
            'Full Context Mode',
            'Use the full document as context instead of retrieved chunks.',
            false,
            { showIf: notBypassed },
          ),
          sw(
            'ENABLE_RAG_HYBRID_SEARCH',
            'Hybrid Search',
            'Combine semantic and keyword retrieval.',
            false,
            { showIf: retrieving },
          ),
          sw(
            'ENABLE_RAG_HYBRID_SEARCH_ENRICHED_TEXTS',
            'Enrich Hybrid Search Text',
            'Add filenames, titles, sections, and snippets to improve lexical recall.',
            false,
            { showIf: hybrid },
          ),
          field(
            'text',
            'RAG_RERANKING_MODEL',
            'Reranking Model',
            'Model used to rerank retrieved results.',
            { showIf: hybrid },
          ),
          field(
            'number',
            'TOP_K',
            'Top K',
            'Maximum number of retrieved chunks returned to the model.',
            { start: 3, placeholder: 'Enter Top K', showIf: retrieving },
          ),
          field(
            'number',
            'TOP_K_RERANKER',
            'Top K Reranker',
            'Maximum number of hybrid results sent to the reranker.',
            { start: 3, placeholder: 'Enter Top K Reranker', showIf: hybrid },
          ),
          field(
            'number',
            'RELEVANCE_THRESHOLD',
            'Relevance Threshold',
            'Only return documents with a score greater than or equal to this value.',
            { start: 0, placeholder: 'Enter Score', showIf: hybrid },
          ),
          field(
            'textarea',
            'RAG_TEMPLATE',
            'RAG Template',
            'Prompt template used when retrieved context is injected.',
            { placeholder: DEFAULT_PROMPT },
          ),
        ],
      },
      {
        heading: 'Files',
        items: [
          field(
            'text',
            'FILE_ALLOWED_EXTENSIONS',
            'Allowed File Extensions',
            'Comma-separated upload extensions. Leave empty for all file types.',
            { placeholder: 'e.g. pdf, docx, txt' },
          ),
          field(
            'number',
            'FILE_MAX_SIZE',
            'Max Upload Size',
            'Maximum file size in MB. Leave empty for unlimited.',
            { placeholder: 'Leave empty for unlimited', half: true },
          ),
          field(
            'number',
            'FILE_MAX_COUNT',
            'Max Upload Count',
            'Maximum number of files that can be used at once in chat.',
            { placeholder: 'Leave empty for unlimited', half: true },
          ),
          field(
            'number',
            'FILE_IMAGE_COMPRESSION_WIDTH',
            'Image Compression Width',
            'Width in pixels to compress images to. Leave empty for no compression.',
            { placeholder: 'Leave empty for no compression', half: true },
          ),
          field(
            'number',
            'FILE_IMAGE_COMPRESSION_HEIGHT',
            'Image Compression Height',
            'Height in pixels to compress images to. Leave empty for no compression.',
            { placeholder: 'Leave empty for no compression', half: true },
          ),
        ],
      },
      {
        heading: 'Danger Zone',
        items: [
          {
            kind: 'action',
            key: 'reset-uploads',
            label: 'Reset Upload Directory',
            note: 'Delete uploaded files from the upload directory.',
            action: 'Reset',
          },
          {
            kind: 'action',
            key: 'reset-vectors',
            label: 'Reset Vector Storage/Knowledge',
            note: 'Clear vector storage and knowledge indexing data.',
            action: 'Reset',
          },
          {
            kind: 'action',
            key: 'reindex',
            label: 'Reindex Knowledge and Memory Vectors',
            note: 'Rebuild vectors for existing knowledge files, knowledge search, and memories.',
            action: 'Reindex',
          },
        ],
      },
    ],
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
