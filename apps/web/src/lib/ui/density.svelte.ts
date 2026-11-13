// The app-wide density on <html data-density>. A region can still set its own data-density, which
// wins inside it (tokens/density.css). app.html applies the stored value before first paint.

export type Density = 'comfortable' | 'default' | 'compact';

const KEY = '4ce.density';
const VALUES: readonly string[] = ['comfortable', 'default', 'compact'];

function stored(): Density {
  try {
    const value = localStorage.getItem(KEY);
    return value && VALUES.includes(value) ? (value as Density) : 'default';
  } catch {
    return 'default'; // Storage is blocked.
  }
}

let current = $state(stored());

function apply() {
  document.documentElement.dataset.density = current;
}

apply();

export const density = {
  get value(): Density {
    return current;
  },
  set value(value: Density) {
    if (!VALUES.includes(value)) return;
    current = value;
    try {
      localStorage.setItem(KEY, value);
    } catch {
      // Storage is blocked: the choice lasts until the page reloads.
    }
    apply();
  },
};
