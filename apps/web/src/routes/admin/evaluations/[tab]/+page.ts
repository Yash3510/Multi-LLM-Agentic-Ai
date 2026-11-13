import type { PageLoad } from './$types';

// Anything but feedback falls back to the leaderboard (admin F93).
export const load: PageLoad = ({ params }) => ({
  tab: params.tab === 'feedback' ? ('feedback' as const) : ('leaderboard' as const),
});
