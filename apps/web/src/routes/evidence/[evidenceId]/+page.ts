import { error } from '@sveltejs/kit';
import { data } from '$lib/data';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, url }) => {
  const evidence = await data.getEvidence(params.evidenceId);
  if (!evidence) error(404, 'Evidence not found');
  // ?page= opens a page and ?box= one observation on its page, so other screens can point at them.
  const asked = (name: string) => Number(url.searchParams.get(name)) || undefined;
  return { evidence, page: asked('page'), box: asked('box') };
};
