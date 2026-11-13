// The interface preferences (common look F68): sections of rows, each a switch, a button that
// steps through its choices, or a custom value. Rows, order and starting values follow the
// running app's capture account; Toast Notifications for New Updates, the What's New dialog and
// Web Search in Chat are left out, as the owner chose (they reach outside the machine).

export type PrefValue = boolean | string | number | undefined;

export interface PrefRow {
  key: string;
  label: string;
  note: string;
  kind: 'switch' | 'cycle' | 'scale' | 'font' | 'upload' | 'manage';
  start: PrefValue;
  /** For a cycle: [value, button text] in order. */
  choices?: [string, string][];
}

const on = (key: string, label: string, note: string): PrefRow => ({
  key,
  label,
  note,
  kind: 'switch',
  start: true,
});
const off = (key: string, label: string, note: string): PrefRow => ({
  ...on(key, label, note),
  start: false,
});
const cycleRow = (
  key: string,
  label: string,
  note: string,
  choices: [string, string][],
): PrefRow => ({ key, label, note, kind: 'cycle', start: choices[0][0], choices });

export const SECTIONS: { heading: string; rows: PrefRow[] }[] = [
  {
    heading: '4CE',
    rows: [
      on(
        'trustView',
        'Trust view in answers',
        'Underline each sentence of an answer by what it rests on: a source, a figure 4CE checked, or nothing that could be checked. Hover a sentence to see why.',
      ),
      on(
        'routePreview',
        'Show the route as you type',
        'Under the message box, show which agents a request will go through before you send it.',
      ),
    ],
  },
  {
    heading: 'UI',
    rows: [
      {
        key: 'uiScale',
        label: 'UI Scale',
        note: 'Set a local zoom level for the app interface.',
        kind: 'scale',
        start: undefined,
      },
      {
        key: 'fontFamily',
        label: 'Font Family',
        note: 'Use a local font family for the app interface.',
        kind: 'font',
        start: undefined,
      },
      off(
        'accessibility',
        'Accessibility Mode',
        'Enable accessibility-focused visual enhancements.',
      ),
      on(
        'chatTitleInTab',
        'Display Chat Title in Tab',
        'Use the active chat title as the browser tab title.',
      ),
      off(
        'userLocation',
        'Allow User Location',
        'Share your current location with features that can use it.',
      ),
      off(
        'haptics',
        'Haptic Feedback (Android)',
        'Use haptic feedback on supported Android devices.',
      ),
      off(
        'copyFormatted',
        'Copy Formatted Text',
        'Copy rich formatted content instead of plain text.',
      ),
    ],
  },
  {
    heading: 'Chat',
    rows: [
      on(
        'messageQueue',
        'Enable Message Queue',
        'Queue outgoing messages instead of interrupting active responses.',
      ),
      cycleRow(
        'chatDirection',
        'Chat Direction',
        'Choose automatic, left-to-right, or right-to-left text flow.',
        [
          ['auto', 'Auto'],
          ['ltr', 'LTR'],
          ['rtl', 'RTL'],
        ],
      ),
      cycleRow(
        'landingMode',
        'Landing Page Mode',
        'Choose whether the app opens to the default home or chat view.',
        [
          ['default', 'Default'],
          ['chat', 'Chat'],
        ],
      ),
      {
        key: 'chatBackground',
        label: 'Chat Background Image',
        note: 'Upload or reset the image shown behind chat content.',
        kind: 'upload',
        start: undefined,
      },
      on('chatBubble', 'Chat Bubble UI', 'Render messages in compact bubble containers.'),
      off('widescreen', 'Widescreen Mode', 'Use a wider chat layout on large displays.'),
      off(
        'temporaryDefault',
        'Temporary Chat by Default',
        'Start new chats as temporary unless changed.',
      ),
      on('fadeStreaming', 'Fade Effect for Streaming Text', 'Fade streaming text as it arrives.'),
      on(
        'markdownUser',
        'Render Markdown in User Messages',
        'Format Markdown syntax in your own messages.',
      ),
      on(
        'markdownAssistant',
        'Render Markdown in Assistant Messages',
        'Format Markdown syntax in assistant responses.',
      ),
      on(
        'markdownPreviews',
        'Render Markdown in Previews',
        'Format Markdown in previews and compact content surfaces.',
      ),
      on(
        'autoTitle',
        'Title Auto-Generation',
        'Generate chat titles automatically from conversation content.',
      ),
      on(
        'autoFollowUps',
        'Follow-Up Auto-Generation',
        'Generate suggested follow-up prompts after responses.',
      ),
      on('autoTags', 'Chat Tags Auto-Generation', 'Generate tags for chats automatically.'),
      off(
        'autoCopy',
        'Auto-Copy Response to Clipboard',
        'Copy the latest assistant response when it completes.',
      ),
      on('autoScroll', 'Response Auto-Scroll', 'Follow assistant responses as they are generated.'),
      on(
        'scrollOnBranch',
        'Scroll On Branch Change',
        'Scroll to the active branch when switching response branches.',
      ),
      off(
        'insertSuggestion',
        'Insert Suggestion Prompt to Input',
        'Place selected suggestion text into the composer.',
      ),
      off(
        'keepFollowUps',
        'Keep Follow-Up Prompts in Chat',
        'Keep generated follow-up prompts visible in the chat.',
      ),
      off(
        'insertFollowUp',
        'Insert Follow-Up Prompt to Input',
        'Insert selected follow-up prompts directly into the composer.',
      ),
      on(
        'regenerateMenu',
        'Regenerate Menu',
        'Show the regenerate action menu for assistant responses.',
      ),
      off('collapseCode', 'Always Collapse Code Blocks', 'Collapse code blocks by default.'),
      off('expandDetails', 'Always Expand Details', 'Open detail blocks by default.'),
      on(
        'hoverPreviews',
        'Chat Hover Previews',
        'Show a floating preview of recent messages when hovering a chat in the sidebar.',
      ),
      off(
        'multiModelTabs',
        'Display Multi-model Responses in Tabs',
        'Group multi-model responses into tabs.',
      ),
      cycleRow(
        'terminalDisplay',
        'Terminal File Display',
        'Choose where terminal display_file results appear by default.',
        [
          ['sidebar', 'Sidebar'],
          ['inline', 'Inline'],
        ],
      ),
      on(
        'filesOnTerminal',
        'Show Files on Terminal Select',
        'Open the file browser after selecting a terminal.',
      ),
      off(
        'terminalSameOrigin',
        'Terminal Preview Allow Same Origin',
        'Allow terminal previews to access same-origin browser APIs.',
      ),
      on(
        'stylizedPdf',
        'Stylized PDF Export',
        'Use styled formatting when exporting chats to PDF.',
      ),
      {
        key: 'quickActions',
        label: 'Floating Quick Actions',
        note: 'Show the floating quick-action toolbar in chat.',
        kind: 'manage',
        start: true,
      },
    ],
  },
  {
    heading: 'Input',
    rows: [
      cycleRow(
        'enterBehavior',
        'Enter Key Behavior',
        'Choose whether Enter sends immediately or uses Ctrl+Enter.',
        [
          ['enter', 'Enter to Send'],
          ['ctrl-enter', 'Ctrl+Enter to Send'],
        ],
      ),
      on(
        'richText',
        'Rich Text Input for Chat',
        'Use the rich composer instead of a plain textarea.',
      ),
      off(
        'formattingToolbar',
        'Show Formatting Toolbar',
        'Show formatting controls in the rich text composer.',
      ),
      off(
        'promptRichText',
        'Insert Prompt as Rich Text',
        'Paste inserted prompts as rich text when possible.',
      ),
      off(
        'largePasteAsFile',
        'Paste Large Text as File',
        'Convert long pasted text into a file attachment.',
      ),
    ],
  },
  {
    heading: 'Artifacts',
    rows: [
      on(
        'detectArtifacts',
        'Detect Artifacts Automatically',
        'Detect generated artifacts and show them in the artifact workspace.',
      ),
      on(
        'sandboxScripts',
        'iframe Sandbox Allow Scripts',
        'Allow scripts inside sandboxed iframes.',
      ),
      off(
        'sandboxSameOrigin',
        'iframe Sandbox Allow Same Origin',
        'Allow artifacts to access same-origin browser APIs inside the sandbox.',
      ),
      on(
        'sandboxForms',
        'iframe Sandbox Allow Forms',
        'Allow forms inside sandboxed artifact iframes.',
      ),
      on(
        'sandboxDownloads',
        'iframe Sandbox Allow Downloads',
        'Allow downloads inside sandboxed iframes.',
      ),
    ],
  },
  {
    heading: 'Voice',
    rows: [
      off(
        'voiceInterrupt',
        'Allow Voice Interruption in Call',
        'Let speech interrupt the assistant during a voice call.',
      ),
      off('callEmoji', 'Display Emoji in Call', 'Show emoji feedback in the call interface.'),
    ],
  },
  {
    heading: 'File',
    rows: [
      cycleRow(
        'uploadMode',
        'Default Upload Mode',
        'Attach files with full content or focused retrieval by default.',
        [
          ['retrieval', 'Using Focused Retrieval'],
          ['full', 'Using Entire Document'],
        ],
      ),
      {
        key: 'imageCompression',
        label: 'Image Compression',
        note: 'Compress uploaded images before sending or storage.',
        kind: 'manage',
        start: false,
      },
    ],
  },
];

/** Every row's starting value, by key. */
export const defaults = (): Record<string, PrefValue> =>
  Object.fromEntries(
    SECTIONS.flatMap((section) => section.rows.map((row) => [row.key, row.start])),
  );

/** The next choice of a cycle button. */
export function cycle(row: PrefRow, value: PrefValue): string {
  const choices = row.choices ?? [];
  const at = choices.findIndex(([choice]) => choice === value);
  return choices[(at + 1) % choices.length][0];
}

/** A cycle button's text for a value. */
export const choiceLabel = (row: PrefRow, value: PrefValue) =>
  row.choices?.find(([choice]) => choice === value)?.[1] ?? '';

/** The UI Scale button: Default, or the custom scale like "1.2x". */
export const scaleLabel = (scale: PrefValue) =>
  typeof scale === 'number' ? `${scale}x` : 'Default';
