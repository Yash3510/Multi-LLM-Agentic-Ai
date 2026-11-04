// Stand-in conversations for the shell until the chat API lands (WP-RT-01). Sector-neutral:
// rules R2 to R6, ids like CASE-0142. Times are relative to when the page loads.
export interface DemoMessage {
  role: 'user' | 'response';
  text: string;
  at: Date;
  /** Response status line, e.g. "Answered directly". */
  status?: string;
  /** A direct reply's model and duration. */
  direct?: { model: string; seconds: number };
}

export interface DemoChat {
  id: string;
  title: string;
  updated: Date;
  /** How the last run ended: the sidebar's run marker. */
  outcome?: 'released' | 'withheld' | 'interrupted' | 'done' | 'direct';
  messages?: DemoMessage[];
}

const hoursAgo = (hours: number) => new Date(Date.now() - hours * 3_600_000);

export const DEMO_CHATS: DemoChat[] = [
  {
    id: 'c-0142',
    title: 'Is R2 · Ratio within the limit for CASE-0142?',
    updated: hoursAgo(2),
    outcome: 'released',
    messages: [
      { role: 'user', text: 'Is R2 · Ratio within the limit for CASE-0142?', at: hoursAgo(2.1) },
      {
        role: 'response',
        text: 'Yes. **R2 · Ratio** for CASE-0142 is 82.5 %, against a limit of 85 %.\n\n| Batch | Ratio | Limit |\n| --- | ---: | ---: |\n| Second | 82.5 % | 85 % |\n\n- The reading comes from the second batch report.\n- The first batch had no ratio recorded.',
        at: hoursAgo(2),
      },
    ],
  },
  {
    id: 'c-0143',
    title: 'Review the duration readings for CASE-0143',
    updated: hoursAgo(30),
    outcome: 'released',
  },
  {
    id: 'c-0139',
    title: 'Cost of the second batch against R4',
    updated: hoursAgo(4 * 24),
    outcome: 'released',
  },
  {
    id: 'c-0131',
    title: 'Draft an approval note for CASE-0131',
    updated: hoursAgo(12 * 24),
    outcome: 'released',
  },
  {
    id: 'c-hi',
    title: 'hi',
    updated: hoursAgo(21 * 24),
    outcome: 'direct',
    messages: [
      { role: 'user', text: 'hi', at: hoursAgo(21 * 24) },
      {
        role: 'response',
        text: 'Hello. What can I help you with?',
        at: hoursAgo(21 * 24),
        status: 'Answered directly',
        direct: { model: 'qwen/qwen3-1.7b', seconds: 7.9 },
      },
    ],
  },
  {
    id: 'c-0120',
    title: 'Audit this deployment for sovereignty',
    updated: hoursAgo(40 * 24),
    outcome: 'released',
  },
];
