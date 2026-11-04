// Stand-in conversations for the shell until the chat API lands (WP-RT-01). Sector-neutral:
// rules R2 to R6, ids like CASE-0142. Times are relative to when the page loads.
export interface DemoMessage {
  role: 'user' | 'response';
  text: string;
  at: Date;
}

export interface DemoChat {
  id: string;
  title: string;
  updated: Date;
  messages?: DemoMessage[];
}

const hoursAgo = (hours: number) => new Date(Date.now() - hours * 3_600_000);

export const DEMO_CHATS: DemoChat[] = [
  {
    id: 'c-0142',
    title: 'Is R2 · Ratio within the limit for CASE-0142?',
    updated: hoursAgo(2),
    messages: [
      { role: 'user', text: 'Is R2 · Ratio within the limit for CASE-0142?', at: hoursAgo(2.1) },
      {
        role: 'response',
        text: 'Yes. **R2 · Ratio** for CASE-0142 is 82.5 %, against a limit of 85 %.\n\n| Batch | Ratio | Limit |\n| --- | ---: | ---: |\n| Second | 82.5 % | 85 % |\n\n- The reading comes from the second batch report.\n- The first batch had no ratio recorded.',
        at: hoursAgo(2),
      },
    ],
  },
  { id: 'c-0143', title: 'Review the duration readings for CASE-0143', updated: hoursAgo(30) },
  { id: 'c-0139', title: 'Cost of the second batch against R4', updated: hoursAgo(4 * 24) },
  { id: 'c-0131', title: 'Draft an approval note for CASE-0131', updated: hoursAgo(12 * 24) },
  { id: 'c-0120', title: 'Audit this deployment for sovereignty', updated: hoursAgo(40 * 24) },
];
