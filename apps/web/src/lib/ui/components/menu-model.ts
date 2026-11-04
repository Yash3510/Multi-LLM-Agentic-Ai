// What a Menu shows, as data, and the pure rules for nested choices. A nested list never opens a
// flyout: choosing its row drills in, so the same panel shows the nested entries under a back row.
import type { IconName } from '$lib/ui/icons/generated/icons';

/** A command. Named by verb and object ("Copy case id"); a shortcut shows as key caps. */
export interface MenuAction {
  type?: 'action';
  id: string;
  label: string;
  icon?: IconName;
  /** Keys by name, as Kbd takes them. Shown and announced; the caller still binds the keys. */
  shortcut?: string[];
  disabled?: boolean;
  /** Why it is disabled, shown under the label. */
  reason?: string;
  /** Destructive: drawn in stop ink. */
  danger?: boolean;
  onSelect?: () => void;
}

/** A row that drills into nested entries within the same panel. */
export interface MenuDrill {
  type: 'drill';
  id: string;
  label: string;
  icon?: IconName;
  disabled?: boolean;
  items: MenuEntry[];
}

export interface MenuOption {
  value: string;
  label: string;
  icon?: IconName;
  disabled?: boolean;
}

/** One-of choices (menuitemradio). The chosen one takes the selected look and a tick. */
export interface MenuChoices {
  type: 'choices';
  id: string;
  /** Names the group for assistive technology. */
  label: string;
  value: string;
  options: MenuOption[];
  onChange: (value: string) => void;
}

export interface MenuSeparator {
  type: 'separator';
}

/** A titled group of rows (role group, with a visible heading). */
export interface MenuGroup {
  type: 'group';
  id: string;
  label: string;
  items: Exclude<MenuEntry, MenuGroup>[];
}

export type MenuEntry = MenuAction | MenuDrill | MenuChoices | MenuSeparator | MenuGroup;

export interface MenuLevel {
  /** The entries to show. */
  entries: MenuEntry[];
  /** The drill rows passed through, outermost first; empty at the top level. */
  trail: MenuDrill[];
}

const isDrill = (entry: MenuEntry): entry is MenuDrill => entry.type === 'drill';

/** The rows of a level with its groups opened up, in order. */
export function flatRows(entries: MenuEntry[]): MenuEntry[] {
  return entries.flatMap((entry) => (entry.type === 'group' ? entry.items : [entry]));
}

/**
 * The level a path of drill ids leads to. The path stops at the first id that is missing or
 * disabled, so a list that changed underneath an open menu falls back to the deepest valid level.
 */
export function levelAt(entries: MenuEntry[], path: readonly string[]): MenuLevel {
  const trail: MenuDrill[] = [];
  let current = entries;
  for (const id of path) {
    const next = flatRows(current).find(
      (entry): entry is MenuDrill => isDrill(entry) && entry.id === id,
    );
    if (!next || next.disabled) break;
    trail.push(next);
    current = next.items;
  }
  return { entries: current, trail };
}

/** The current choice inside a drill row, shown at the row's end: "Density · Default". */
export function drillHint(drill: MenuDrill): string | undefined {
  const choices = flatRows(drill.items).find(
    (entry): entry is MenuChoices => entry.type === 'choices',
  );
  return choices?.options.find((option) => option.value === choices.value)?.label;
}

/** The trail that is valid for these entries, so a stale path never points at nothing. */
export function validPath(entries: MenuEntry[], path: readonly string[]): string[] {
  return levelAt(entries, path).trail.map((drill) => drill.id);
}

/** Whether any row of a level has an icon, so every label in it lines up after one icon column. */
export function hasIcons(entries: MenuEntry[]): boolean {
  return flatRows(entries).some((entry) =>
    entry.type === 'choices'
      ? entry.options.some((option) => option.icon)
      : entry.type !== 'separator' && entry.type !== 'group' && !!entry.icon,
  );
}
