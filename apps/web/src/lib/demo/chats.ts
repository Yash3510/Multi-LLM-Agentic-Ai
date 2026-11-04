// Stand-in conversations for the shell until the chat API lands (WP-RT-01). Sector-neutral:
// rules R2 to R6, ids like CASE-0142. Times are relative to when the page loads.
export interface DemoChat {
  id: string;
  title: string;
  updated: Date;
}

const hoursAgo = (hours: number) => new Date(Date.now() - hours * 3_600_000);

export const DEMO_CHATS: DemoChat[] = [
  { id: 'c-0142', title: 'Is R2 · Ratio within the limit for CASE-0142?', updated: hoursAgo(2) },
  { id: 'c-0143', title: 'Review the duration readings for CASE-0143', updated: hoursAgo(30) },
  { id: 'c-0139', title: 'Cost of the second batch against R4', updated: hoursAgo(4 * 24) },
  { id: 'c-0131', title: 'Draft an approval note for CASE-0131', updated: hoursAgo(12 * 24) },
  { id: 'c-0120', title: 'Audit this deployment for sovereignty', updated: hoursAgo(40 * 24) },
];
