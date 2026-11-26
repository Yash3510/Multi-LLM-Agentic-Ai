import { error } from '@sveltejs/kit';
import { data } from '$lib/data';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params }) => {
  const run = await data.getRun(params.runId);
  if (!run) error(404, 'Run not found');
  return { run };
};
