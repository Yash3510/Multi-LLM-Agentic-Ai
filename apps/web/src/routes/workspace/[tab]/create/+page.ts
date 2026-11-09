import { error } from '@sveltejs/kit';
import { data } from '$lib/data';
import type { PageLoad } from './$types';

// Each tab's create page (workspace F32, F56). The model editor waits for its lookups first
// (F34); Knowledge opens its create dialog over the list.
export const load: PageLoad = async ({ params }) => {
  if (params.tab === 'models') {
    const [baseModels, knowledge, tools, skills] = await Promise.all([
      data.listBaseModels(),
      data.listKnowledge(),
      data.listTools(),
      data.listSkills(),
    ]);
    // Switched-off skills are not offered in the editor's picker (F44).
    const active = skills.filter((skill) => skill.active);
    return { tab: 'models' as const, editor: { baseModels, knowledge, tools, skills: active } };
  }
  if (params.tab === 'knowledge') {
    return { tab: 'knowledge' as const, bases: await data.listKnowledge() };
  }
  if (params.tab === 'skills') return { tab: 'skills' as const };
  if (params.tab === 'prompts') {
    return { tab: 'prompts' as const, prompts: await data.listPrompts() };
  }
  error(404, 'Not found');
};
