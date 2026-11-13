import { redirect } from '@sveltejs/kit';
import type { LayoutLoad } from './$types';

// The admin pages are for admins only; anyone else goes home (admin F1).
export const load: LayoutLoad = async ({ parent }) => {
  const { user } = await parent();
  if (user?.role !== 'admin') redirect(307, '/');
};
