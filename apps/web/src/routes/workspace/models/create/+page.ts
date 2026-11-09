import { data } from '$lib/data';
import type { PageLoad } from './$types';

// The editor waits for its lookups before it shows (workspace F34).
export const load: PageLoad = async () => {
  const [baseModels, knowledge, tools, skills] = await Promise.all([
    data.listBaseModels(),
    data.listKnowledge(),
    data.listTools(),
    data.listSkills(),
  ]);
  return { baseModels, knowledge, tools, skills };
};
