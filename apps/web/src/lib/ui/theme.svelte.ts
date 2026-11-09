// The theme: the user's choice and the theme it resolves to on <html data-theme>.
// app.html sets the same attributes before first paint; this module keeps them in step afterwards.

/** OLED Dark is dark with its darkest greys set to black (general settings, chat-composer §9.3). */
export type ThemeChoice = 'system' | 'light' | 'dark' | 'oled-dark';
export type ResolvedTheme = 'light' | 'dark';

const KEY = '4ce.theme';
const CHOICES: readonly string[] = ['system', 'light', 'dark', 'oled-dark'];

function stored(): ThemeChoice {
  try {
    const value = localStorage.getItem(KEY);
    return value && CHOICES.includes(value) ? (value as ThemeChoice) : 'system';
  } catch {
    return 'system'; // Storage is blocked: follow the system.
  }
}

// Optional because jsdom, which component tests run in, has no matchMedia.
const systemQuery = globalThis.matchMedia?.('(prefers-color-scheme: dark)');

let choice = $state(stored());
let systemDark = $state(systemQuery?.matches ?? false);

const resolve = (): ResolvedTheme =>
  choice === 'system' ? (systemDark ? 'dark' : 'light') : choice === 'oled-dark' ? 'dark' : choice;

function apply() {
  const resolved = resolve();
  document.documentElement.dataset.theme = resolved;
  document.documentElement.style.colorScheme = resolved;
  document.documentElement.toggleAttribute('data-oled', choice === 'oled-dark');
}

systemQuery?.addEventListener('change', (event) => {
  systemDark = event.matches;
  apply();
});
apply();

export const theme = {
  get choice(): ThemeChoice {
    return choice;
  },
  set choice(value: ThemeChoice) {
    if (!CHOICES.includes(value)) return;
    choice = value;
    try {
      localStorage.setItem(KEY, value);
    } catch {
      // Storage is blocked: the choice lasts until the page reloads.
    }
    apply();
  },
  get resolved(): ResolvedTheme {
    return resolve();
  },
};
