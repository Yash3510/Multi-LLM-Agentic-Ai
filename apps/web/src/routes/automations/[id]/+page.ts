import { error } from '@sveltejs/kit';
import { data } from '$lib/data';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params }) => {
  const automation = await data.getAutomation(params.id);
  if (!automation) error(404, 'Not found');
  return { automation };
};
