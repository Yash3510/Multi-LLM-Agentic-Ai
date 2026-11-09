import { error, redirect } from '@sveltejs/kit';
import { data } from '$lib/data';
import type { PageLoad } from './$types';

// A knowledge base (workspace F66): a missing one goes back to the list.
export const load: PageLoad = async ({ params }) => {
  if (params.tab !== 'knowledge') error(404, 'Not found');
  const base = await data.getKnowledge(params.id);
  if (!base) redirect(307, '/workspace/knowledge');
  return { base };
};
