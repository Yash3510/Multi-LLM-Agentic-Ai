import { error } from '@sveltejs/kit';
import { data } from '$lib/data';
import type { WorkspaceTab } from '$lib/data';
import type { PageLoad } from './$types';

const TABS: WorkspaceTab[] = ['models', 'knowledge', 'prompts', 'skills', 'tools'];
const isTab = (value: string): value is WorkspaceTab => TABS.some((tab) => tab === value);

export const load: PageLoad = async ({ params }) => {
  if (!isTab(params.tab)) error(404, 'Not found');
  const [counts, models] = await Promise.all([data.workspaceCounts(), data.listModels()]);
  return { tab: params.tab, counts, models };
};
