import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = ({ params }) => {
  if (params.tab !== 'overview' && params.tab !== 'groups') error(404, 'Not found');
  return { tab: params.tab };
};
