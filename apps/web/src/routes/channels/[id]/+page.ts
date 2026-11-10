import { error } from '@sveltejs/kit';
import { data } from '$lib/data';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params }) => {
  const channel = await data.getChannel(params.id);
  if (!channel) error(404, 'Not found');
  return { channel };
};
