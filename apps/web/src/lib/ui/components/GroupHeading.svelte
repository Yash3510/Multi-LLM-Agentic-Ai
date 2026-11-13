<script module lang="ts">
  import { m } from '$lib/i18n/generated/messages.js';
  import type { TimeGroup } from '$lib/ui/format';

  const BAND = {
    today: m.list_group_today,
    yesterday: m.list_group_yesterday,
    week: m.list_group_week,
    month: m.list_group_month,
  };

  /** The band's name: the fixed bands from messages, a month by its full name in the locale, a
   * year as plain digits. */
  export function groupLabel(group: TimeGroup, locale: string): string {
    if (group.band === 'month-name')
      return new Intl.DateTimeFormat(locale, { month: 'long' }).format(new Date(2000, group.month));
    if (group.band === 'year') return String(group.year);
    return BAND[group.band]();
  }
</script>

<script lang="ts">
  // The heading above the first row of each recency band (layout look §4.2, §9.2): 12 px muted
  // ink, extra room above every band but the first. A real heading, so assistive technology can
  // move between bands.
  import { getLocale } from '$lib/i18n/generated/runtime.js';
  import { toIntlLocale } from '$lib/ui/format';

  type Props = {
    group: TimeGroup;
    /** The first band sits flush with the top of the list. */
    first?: boolean;
    /** `sidebar` for the side list, `dialog` for list dialogs; the measured paddings differ. */
    variant?: 'sidebar' | 'dialog';
    /** The heading level within the page. */
    level?: 2 | 3 | 4;
  };

  let { group, first = false, variant = 'dialog', level = 3 }: Props = $props();

  const locale = toIntlLocale(getLocale());
</script>

<svelte:element
  this={`h${level}`}
  class="group-heading"
  data-variant={variant}
  data-first={first ? '' : undefined}
>
  {groupLabel(group, locale)}
</svelte:element>

<style>
  .group-heading {
    inline-size: 100%;
    color: var(--color-ink-3);
    font-size: var(--text-caption);
    font-weight: var(--font-weight-normal);
    line-height: var(--text-caption--line-height);
  }

  .group-heading[data-variant='sidebar'] {
    padding: var(--spacing-4) 0 var(--spacing-1) 10px;
  }

  .group-heading[data-variant='dialog'] {
    padding: var(--spacing-5) var(--spacing-2) var(--spacing-2);
  }

  .group-heading[data-first] {
    padding-block-start: 0;
  }
</style>
