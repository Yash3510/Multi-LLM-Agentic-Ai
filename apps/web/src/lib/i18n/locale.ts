import { defineCustomClientStrategy, getLocale } from './generated/runtime.js';

// Paraglide's built-in localStorage strategy throws where storage is blocked, so the
// locale is stored under the app's own key with the same guard as theme and motion.
const KEY = '4ce.locale';

// Where storage is blocked, a choice still holds until the page reloads.
let chosen: string | undefined;

defineCustomClientStrategy('custom-storage', {
  getLocale: () => {
    try {
      return localStorage.getItem(KEY) ?? chosen;
    } catch {
      return chosen;
    }
  },
  setLocale: (locale) => {
    chosen = locale;
    // setLocale(..., { reload: false }) switches without a reload, so the page language follows here.
    document.documentElement.lang = locale;
    try {
      localStorage.setItem(KEY, locale);
    } catch {
      // Storage is blocked: the choice lasts until the page reloads.
    }
  },
});

document.documentElement.lang = getLocale();
