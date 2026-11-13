import { error } from '@sveltejs/kit';
import { data } from '$lib/data';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params }) => {
  const note = await data.getNote(params.id);
  if (!note) error(404, 'Not found');
  return { note };
};
