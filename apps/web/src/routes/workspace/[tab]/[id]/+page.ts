import { error, redirect } from '@sveltejs/kit';
import { data } from '$lib/data';
import type { PageLoad } from './$types';

// A knowledge base (workspace F66) or a prompt (F95); a missing one goes back to its list.
export const load: PageLoad = async ({ params }) => {
  if (params.tab === 'knowledge') {
    const base = await data.getKnowledge(params.id);
    if (!base) redirect(307, '/workspace/knowledge');
    return { tab: 'knowledge' as const, base };
  }
  if (params.tab === 'prompts') {
    const prompt = await data.getPrompt(params.id);
    if (!prompt) redirect(307, '/workspace/prompts');
    return { tab: 'prompts' as const, prompt };
  }
  error(404, 'Not found');
};
