import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

// /workspace opens on its first tab, as the running app does.
export const load: PageLoad = () => redirect(307, '/workspace/models');
