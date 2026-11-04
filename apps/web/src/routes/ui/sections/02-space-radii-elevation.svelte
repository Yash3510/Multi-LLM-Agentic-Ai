<script module lang="ts">
  import { m } from '$lib/i18n/generated/messages.js';
  import type { SectionMeta } from '../section';

  export const section: SectionMeta = {
    id: 'space',
    title: m.ui_section_space,
    description: m.ui_space_intro,
  };
</script>

<script lang="ts">
  import { formatNumber } from '$lib/ui/format';

  // Class names are written out in full so Tailwind finds them.
  const SPACING = [
    { px: 2, class: 'size-0.5' },
    { px: 4, class: 'size-1' },
    { px: 6, class: 'size-1.5' },
    { px: 8, class: 'size-2' },
    { px: 12, class: 'size-3' },
    { px: 16, class: 'size-4' },
    { px: 20, class: 'size-5' },
    { px: 24, class: 'size-6' },
    { px: 32, class: 'size-8' },
    { px: 40, class: 'size-10' },
    { px: 48, class: 'size-12' },
  ];

  const INSETS = [
    { token: 'inset-row', px: 12, class: 'p-inset-row' },
    { token: 'inset-card', px: 16, class: 'p-inset-card' },
    { token: 'inset-panel', px: 24, class: 'p-inset-panel' },
  ];

  const DENSITIES = [
    { value: 'comfortable', height: 40, label: m.density_comfortable },
    { value: 'default', height: 32, label: m.density_default },
    { value: 'compact', height: 28, label: m.density_compact },
  ];

  const ROWS = [
    { id: 'CASE-0142', rule: 'R2', ratio: 0.82 },
    { id: 'CASE-0143', rule: 'R2', ratio: 0.91 },
    { id: 'CASE-0144', rule: 'R5', ratio: 0.47 },
  ];

  const RADII = [
    { token: 'panel', value: '20', class: 'rounded-panel' },
    { token: 'card', value: '16', class: 'rounded-card' },
    { token: 'inset', value: '12', class: 'rounded-inset' },
    { token: 'control', value: '8', class: 'rounded-control' },
    { token: 'tight', value: '6', class: 'rounded-tight' },
    { token: 'pill', value: 'full', class: 'rounded-pill' },
  ];

  // Each pair obeys inner = outer − padding.
  const NESTED = [
    {
      outer: 'panel 20',
      padding: 8,
      inner: 'inset 12',
      class: 'rounded-panel p-2',
      innerClass: 'rounded-inset',
    },
    {
      outer: 'card 16',
      padding: 4,
      inner: 'inset 12',
      class: 'rounded-card p-1',
      innerClass: 'rounded-inset',
    },
    {
      outer: 'card 16',
      padding: 8,
      inner: 'control 8',
      class: 'rounded-card p-2',
      innerClass: 'rounded-control',
    },
  ];

  const ELEVATIONS = [
    { level: 'e0', use: m.ui_space_e0, class: 'border border-line-1 shadow-e0' },
    { level: 'e1', use: m.ui_space_e1, class: 'border border-line-2 shadow-e1' },
    { level: 'e2', use: m.ui_space_e2, class: 'border border-line-1 shadow-e2' },
    { level: 'e3', use: m.ui_space_e3, class: 'shadow-e3' },
  ];
</script>

<div class="flex flex-col gap-10">
  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">{m.ui_space_scale()}</h3>
    <ol class="flex flex-wrap items-end gap-x-5 gap-y-4">
      {#each SPACING as step (step.px)}
        <li class="flex flex-col items-center gap-2">
          <span class="bg-line-control {step.class}"></span>
          <span class="font-mono text-caption text-ink-3 tabular">{step.px}</span>
        </li>
      {/each}
    </ol>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">{m.ui_space_insets()}</h3>
    <ul class="grid items-start gap-4 md:grid-cols-3">
      {#each INSETS as inset (inset.token)}
        <li class="rounded-inset border border-line-1 bg-surface-sunken {inset.class}">
          <!-- Square: the padding is at least the outer radius, so inner = outer − padding is 0. -->
          <span class="flex h-12 items-center justify-between bg-surface-raised px-3">
            <code class="font-mono text-small text-ink-1">{inset.token}</code>
            <span class="font-mono text-caption text-ink-3 tabular">{inset.px}</span>
          </span>
        </li>
      {/each}
    </ul>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">{m.ui_space_density()}</h3>
    <ul class="grid gap-4 md:grid-cols-3">
      {#each DENSITIES as { value, height, label } (value)}
        <!-- data-density on the region: the rows inside take its height, whatever the page's. -->
        <li class="flex flex-col gap-2" data-density={value}>
          <p class="flex items-baseline justify-between text-caption">
            <span class="text-ink-1">{label()}</span>
            <span class="text-ink-3 tabular">{m.ui_space_density_row({ height })}</span>
          </p>
          <ol class="rounded-inset border border-line-1 bg-surface-raised">
            {#each ROWS as row, index (row.id)}
              <li
                class="flex h-row items-center gap-3 px-3 {index > 0
                  ? 'border-t border-line-1'
                  : ''}"
              >
                <code class="font-mono text-ink-1">{row.id}</code>
                <span class="text-ink-2">{row.rule}</span>
                <span class="ms-auto text-ink-1 tabular"
                  >{formatNumber(row.ratio, { decimals: 2 })}</span
                >
              </li>
            {/each}
          </ol>
        </li>
      {/each}
    </ul>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">{m.ui_space_radii()}</h3>
    <ul class="grid grid-cols-3 gap-4 md:grid-cols-6">
      {#each RADII as radius (radius.token)}
        <li class="flex flex-col gap-2">
          <span class="aspect-video border border-line-2 bg-surface-raised {radius.class}"></span>
          <span class="flex items-baseline justify-between gap-2">
            <code class="font-mono text-small text-ink-1">{radius.token}</code>
            <span class="font-mono text-caption text-ink-3 tabular">{radius.value}</span>
          </span>
        </li>
      {/each}
    </ul>
    <p class="pt-2 text-caption text-ink-3">{m.ui_space_nesting()}</p>
    <ul class="grid items-start gap-4 md:grid-cols-3">
      {#each NESTED as nested (nested.class)}
        <li class="flex flex-col gap-2">
          <span class="flex border border-line-2 bg-surface-sunken {nested.class}">
            <span class="h-12 w-full border border-line-1 bg-surface-raised {nested.innerClass}"
            ></span>
          </span>
          <span class="font-mono text-caption text-ink-3 tabular">
            {nested.outer} − {nested.padding} = {nested.inner}
          </span>
        </li>
      {/each}
    </ul>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">{m.ui_space_elevation()}</h3>
    <ul class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
      {#each ELEVATIONS as elevation (elevation.level)}
        <li
          class="elevation flex flex-col justify-center rounded-card bg-surface-raised px-4 {elevation.class}"
        >
          <code class="font-mono text-small text-ink-1">{elevation.level}</code>
          <span class="text-caption text-ink-3">{elevation.use()}</span>
        </li>
      {/each}
    </ul>
  </div>
</div>

<style>
  /* Taller than any spacing step, so the shadows have room to read. */
  .elevation {
    height: calc(var(--spacing-12) * 2);
  }
</style>
