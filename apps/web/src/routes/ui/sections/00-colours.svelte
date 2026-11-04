<script module lang="ts">
  import { m } from '$lib/i18n/generated/messages.js';
  import type { SectionMeta } from '../section';

  export const section: SectionMeta = {
    id: 'colours',
    title: m.ui_section_colour,
    description: m.ui_colour_intro,
  };
</script>

<script lang="ts">
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { formatNumber, formatPercent, MISSING } from '$lib/ui/format';
  import { theme } from '$lib/ui/theme.svelte';

  type Rgba = [number, number, number, number];
  /** min: the ratio a role needs on surface-raised (4.5 for text, 3 for controls). */
  type Swatch = { role: string; min?: number; exempt?: boolean };

  const GROUPS: { title: () => string; swatches: Swatch[] }[] = [
    {
      title: m.ui_colour_neutrals,
      swatches: [
        { role: 'surface-page' },
        { role: 'surface-raised' },
        { role: 'surface-sunken' },
        { role: 'surface-hover' },
        { role: 'line-1' },
        { role: 'line-2' },
        { role: 'line-control', min: 3 },
        { role: 'scrim' },
      ],
    },
    {
      title: m.ui_colour_text,
      swatches: [
        { role: 'ink-1', min: 4.5 },
        { role: 'ink-2', min: 4.5 },
        { role: 'ink-3', min: 4.5 },
        { role: 'ink-disabled', exempt: true },
      ],
    },
    {
      title: m.ui_colour_violet,
      swatches: [
        { role: 'accent', min: 4.5 },
        { role: 'accent-head', min: 3 },
        { role: 'accent-tail' },
        { role: 'accent-soft' },
      ],
    },
    {
      title: m.ui_colour_verdicts,
      swatches: [
        { role: 'ok', min: 4.5 },
        { role: 'ok-mark', min: 3 },
        { role: 'ok-soft' },
        { role: 'caution', min: 4.5 },
        { role: 'caution-mark', min: 3 },
        { role: 'caution-soft' },
        { role: 'stop', min: 4.5 },
        { role: 'stop-soft' },
      ],
    },
  ];

  const TEXT = ['ink-1', 'ink-2', 'ink-3', 'ink-disabled', 'accent', 'ok', 'caution', 'stop'];
  const SURFACES = ['surface-page', 'surface-raised', 'surface-sunken', 'surface-hover'];
  const SOFT: Record<string, string> = {
    accent: 'accent-soft',
    ok: 'ok-soft',
    caution: 'caution-soft',
    stop: 'stop-soft',
  };

  let probe = $state<HTMLElement>();
  let colours = $state<Record<string, Rgba>>({});

  /**
   * What the browser paints for each role, read back from a 1 px canvas: the computed value may be
   * any CSS colour syntax (oklch, color-mix), and the canvas resolves it to 8-bit sRGB.
   */
  function measure(element: HTMLElement): Record<string, Rgba> {
    const context = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
    if (!context) return {};
    const roles = [...GROUPS.flatMap((group) => group.swatches.map((s) => s.role)), 'stop-mark'];
    return Object.fromEntries(
      roles.map((role) => {
        element.style.color = `var(--color-${role})`;
        context.clearRect(0, 0, 1, 1);
        context.fillStyle = getComputedStyle(element).color;
        context.fillRect(0, 0, 1, 1);
        return [role, [...context.getImageData(0, 0, 1, 1).data] as Rgba];
      }),
    );
  }

  $effect(() => {
    void theme.resolved; // Re-measure whenever the theme swaps the tokens.
    if (probe) colours = measure(probe);
  });

  /** Hex, plus the alpha for a translucent role such as the scrim. */
  const value = (colour: Rgba) =>
    colour[3] < 255
      ? `${hex(colour)} · ${formatPercent(colour[3] / 255, { decimals: 0 })}`
      : hex(colour);

  const hex = ([r, g, b]: Rgba) =>
    '#' + [r, g, b].map((c) => c.toString(16).padStart(2, '0')).join('');

  const luminance = ([r, g, b]: Rgba) => {
    const linear = (c: number) => {
      const s = c / 255;
      return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
    };
    return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b);
  };

  /** The WCAG 2 contrast ratio, or undefined until both colours are measured. */
  function ratio(foreground: string, background: string): number | undefined {
    const a = colours[foreground];
    const b = colours[background];
    if (!a || !b) return undefined;
    const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x);
    return (light + 0.05) / (dark + 0.05);
  }

  const formatRatio = (value: number | undefined) =>
    value === undefined ? MISSING : `${formatNumber(value, { decimals: 2 })}:1`;
</script>

<span bind:this={probe} hidden></span>

<div class="flex flex-col gap-8">
  {#each GROUPS as group (group.title)}
    <div class="flex flex-col gap-3">
      <h3 class="text-small font-medium text-ink-1">{group.title()}</h3>
      <ul class="grid grid-cols-2 gap-x-3 gap-y-5 sm:grid-cols-4 xl:grid-cols-8">
        {#each group.swatches as { role, min, exempt } (role)}
          {@const colour = colours[role]}
          {@const onRaised = min ? ratio(role, 'surface-raised') : undefined}
          <li class="flex min-w-0 flex-col gap-2">
            <span
              class="h-12 rounded-inset border border-line-1"
              style:background-color="var(--color-{role})"
            ></span>
            <span class="flex flex-col">
              <code class="truncate font-mono text-small text-ink-1">{role}</code>
              <span class="font-mono text-caption text-ink-3 tabular">
                {colour ? value(colour) : MISSING}
              </span>
              {#if onRaised !== undefined && min}
                <span
                  class="flex items-center gap-1 text-caption tabular {onRaised < min
                    ? 'text-stop'
                    : 'text-ink-2'}"
                >
                  {#if onRaised < min}<Icon name="warning" size={16} />{/if}
                  {formatRatio(onRaised)}
                  <span class="text-ink-3">{m.ui_colour_on_raised()}</span>
                </span>
              {:else if exempt}
                <span class="text-caption text-ink-3">{m.ui_colour_exempt()}</span>
              {/if}
            </span>
          </li>
        {/each}
      </ul>
    </div>
  {/each}

  <div class="flex flex-col gap-3">
    <div class="flex flex-col gap-1">
      <h3 class="text-small font-medium text-ink-1">{m.ui_colour_matrix()}</h3>
      <p class="text-small text-ink-2">{m.ui_colour_matrix_note()}</p>
    </div>
    <div class="overflow-x-auto rounded-inset border border-line-1">
      <table class="w-full border-collapse text-small">
        <thead class="bg-surface-sunken text-left text-caption text-ink-2">
          <tr>
            <th scope="col" class="h-8 px-3 font-medium">{m.ui_colour_role()}</th>
            {#each [...SURFACES, m.ui_colour_soft()] as surface (surface)}
              <th scope="col" class="h-8 px-3 text-right font-mono font-normal">{surface}</th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each TEXT as role (role)}
            {@const exempt = role === 'ink-disabled'}
            <tr class="border-t border-line-1">
              <th scope="row" class="h-row px-3 text-left font-mono font-normal text-ink-1">
                {role}
              </th>
              {#each [...SURFACES, SOFT[role]] as surface, index (index)}
                {@const value = surface ? ratio(role, surface) : undefined}
                {#if surface}
                  <td
                    class="h-row px-3 text-right tabular"
                    style:background-color="var(--color-{surface})"
                    style:color="var(--color-{role})"
                  >
                    <span class="inline-flex items-center gap-1">
                      {#if value !== undefined && value < 4.5 && !exempt}
                        <Icon name="warning" size={16} label={m.ui_colour_below({ min: '4.5' })} />
                      {/if}
                      {formatRatio(value)}
                    </span>
                  </td>
                {:else}
                  <td class="h-row px-3 text-right text-ink-3">{MISSING}</td>
                {/if}
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
</div>
