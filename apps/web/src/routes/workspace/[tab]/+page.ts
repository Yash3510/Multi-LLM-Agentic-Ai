import { error } from '@sveltejs/kit';
import { data } from '$lib/data';
import type { WorkspaceTab } from '$lib/data';
import type { PageLoad } from './$types';

const TABS: WorkspaceTab[] = ['models', 'knowledge', 'prompts', 'skills', 'tools'];
const isTab = (value: string): value is WorkspaceTab => TABS.some((tab) => tab === value);

export const load: PageLoad = async ({ params }) => {
  if (!isTab(params.tab)) error(404, 'Not found');
  const [models, bases, prompts, skills, tools] = await Promise.all([
    params.tab === 'models' ? data.listModels() : [],
    params.tab === 'knowledge' ? data.listKnowledge() : [],
    params.tab === 'prompts' ? data.listPrompts() : [],
    params.tab === 'skills' ? data.listSkills() : [],
    params.tab === 'tools' ? data.listTools() : [],
  ]);
  return { tab: params.tab, models, bases, prompts, skills, tools };
};
