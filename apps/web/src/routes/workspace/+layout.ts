import { data } from '$lib/data';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async () => ({ counts: await data.workspaceCounts() });
