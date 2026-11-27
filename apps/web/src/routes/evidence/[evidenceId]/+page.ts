import { error } from '@sveltejs/kit';
import { data } from '$lib/data';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, url }) => {
  const evidence = await data.getEvidence(params.evidenceId);
  if (!evidence) error(404, 'Evidence not found');
  // ?box= opens with one observation selected, so other screens can point at it.
  return { evidence, box: Number(url.searchParams.get('box')) || undefined };
};
