// Which settings tabs the sidebar lists (ADR-0041 amendment, 2026-11-13): one side at a time,
// Personal or Admin, and a search that looks through every side the person may see. Kept out of
// the dialog so it can be tested without a DOM.

export type Scope = 'personal' | 'admin';

type Group<T> = { caption: string; tabs: T[] };

export const scopeOf = (tab: string): Scope => (tab.startsWith('admin-') ? 'admin' : 'personal');

export function shownGroups<T extends { label: string }>(
  personal: Group<T>[],
  admin: Group<T>[],
  scope: Scope,
  query: string,
  isAdmin: boolean,
): Group<T>[] {
  const needle = query.trim().toLowerCase();
  if (!needle) return isAdmin && scope === 'admin' ? admin : personal;
  return [...personal, ...(isAdmin ? admin : [])]
    .map((group) => ({
      ...group,
      tabs: group.tabs.filter((one) => one.label.toLowerCase().includes(needle)),
    }))
    .filter((group) => group.tabs.length);
}
