// Registers the stored-locale strategy before any message renders.
import '$lib/i18n/locale';
import { redirect } from '@sveltejs/kit';
import { data } from '$lib/data';
import type { LayoutLoad } from './$types';

// A static single-page app served by 4ce-server (ADR-0035 §2): no server rendering, no prerendering.
export const ssr = false;
export const prerender = false;

// Who is signed in, and the sidebar's chat list (web-data-contract.md). Everything but the
// sign-in page and the design reference needs a signed-in person.
export const load: LayoutLoad = async ({ route }) => {
  const open = route.id === '/auth' || route.id?.startsWith('/ui');
  const user = await data.currentUser();
  if (!user && !open) redirect(307, '/auth');
  return { user, chats: user ? await data.listChats() : [] };
};
