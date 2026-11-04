// Registers the stored-locale strategy before any message renders.
import '$lib/i18n/locale';
import { data } from '$lib/data';
import type { LayoutLoad } from './$types';

// A static single-page app served by 4ce-server (ADR-0035 §2): no server rendering, no prerendering.
export const ssr = false;
export const prerender = false;

// The sidebar's chat list, from the data source (web-data-contract.md).
export const load: LayoutLoad = async () => ({ chats: await data.listChats() });
