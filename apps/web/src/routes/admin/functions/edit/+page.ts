import { error } from '@sveltejs/kit';
import { data } from '$lib/data';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ url }) => {
  const fn = await data.getFunction(url.searchParams.get('id') ?? '');
  if (!fn) error(404, 'Not found');
  return { fn };
};
