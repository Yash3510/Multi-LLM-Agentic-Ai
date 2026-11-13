import { error } from '@sveltejs/kit';
import { data } from '$lib/data';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params }) => {
  const chat = await data.getChat(params.id);
  if (!chat) error(404, 'Chat not found');
  return { chat };
};
