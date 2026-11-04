// Registers the stored-locale strategy before any message renders.
import '$lib/i18n/locale';

// A static single-page app served by 4ce-server (ADR-0035 §2): no server rendering, no prerendering.
export const ssr = false;
export const prerender = false;
