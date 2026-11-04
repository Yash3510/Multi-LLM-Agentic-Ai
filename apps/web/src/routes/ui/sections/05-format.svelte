<script module lang="ts">
  import { m } from '$lib/i18n/generated/messages.js';
  import type { SectionMeta } from '../section';

  export const section: SectionMeta = {
    id: 'format',
    title: m.ui_section_numbers,
    description: m.ui_format_intro,
  };
</script>

<script lang="ts">
  import { getLocale } from '$lib/i18n/generated/runtime.js';
  import {
    formatBytes,
    formatDateTime,
    formatDuration,
    formatHashFull,
    formatHashShort,
    formatIso,
    formatLimit,
    formatMoney,
    formatNumber,
    formatPercent,
    formatQuantity,
    formatTime,
    formatTolerance,
    toIntlLocale,
  } from '$lib/ui/format';

  // The page is rebuilt when the locale changes, so reading it once is enough.
  const locale = toIntlLocale(getLocale());
  const o = { locale };

  const hash = '3f9a21c07be4d58e9a0c6f1b2d7e8a94c51f03b6d2e7a8c9f04b1d6e3a7c5b2f';
  const at = new Date('2026-10-08T08:35:00Z');

  const ROWS: [call: string, output: string, mono?: boolean][] = [
    ['formatNumber(123456.5)', formatNumber(123456.5, o)],
    ['formatNumber(-12)', formatNumber(-12, o)],
    ['formatNumber(-0.0001, { decimals: 2 })', formatNumber(-0.0001, { decimals: 2, ...o })],
    ['formatNumber(0.000012)', formatNumber(0.000012, o)],
    ['formatNumber(NaN)', formatNumber(NaN, o)],
    ["formatQuantity(3.74, 's')", formatQuantity(3.74, 's', o)],
    ["formatTolerance(82.5, 0.5, '%')", formatTolerance(82.5, 0.5, '%', o)],
    ["formatLimit('max', 90, '%')", formatLimit('max', 90, '%', o)],
    ["formatLimit('min', 20, '%')", formatLimit('min', 20, '%', o)],
    ['formatPercent(0.125)', formatPercent(0.125, o)],
    ['formatMoney(1234567.5)', formatMoney(1234567.5, o)],
    ['formatMoney(-12.5)', formatMoney(-12.5, o)],
    ['formatDuration(3.74)', formatDuration(3.74, o)],
    ['formatDuration(9.96)', formatDuration(9.96, o)],
    ['formatDuration(65)', formatDuration(65, o)],
    ['formatDuration(3900)', formatDuration(3900, o)],
    ['formatBytes(512)', formatBytes(512, o)],
    ['formatBytes(1500)', formatBytes(1500, o)],
    ['formatBytes(12300000)', formatBytes(12300000, o)],
    ['formatHashShort(hash)', formatHashShort(hash), true],
    ['formatHashFull(hash)', formatHashFull(hash), true],
    ['formatTime(at)', formatTime(at, o)],
    ['formatDateTime(at)', formatDateTime(at, o)],
    ['formatIso(at)', formatIso(at)],
  ];

  /** The characters beyond ASCII in an output, so the special spaces and signs can be seen. */
  const special = (text: string) =>
    [...new Set(text)]
      .filter((char) => char.codePointAt(0)! > 0x7e)
      .map((char) => `U+${char.codePointAt(0)!.toString(16).toUpperCase().padStart(4, '0')}`)
      .join(' ');
</script>

<div class="flex flex-col gap-3">
  <div class="overflow-x-auto rounded-inset border border-line-1">
    <table class="w-full border-collapse text-left text-small">
      <thead class="bg-surface-sunken text-caption text-ink-2">
        <tr>
          <th scope="col" class="h-8 px-3 font-medium">{m.ui_format_call()}</th>
          <th scope="col" class="h-8 px-3 font-medium">{m.ui_format_output({ locale })}</th>
          <th scope="col" class="h-8 px-3 font-medium">{m.ui_format_chars()}</th>
        </tr>
      </thead>
      <tbody data-density="compact">
        {#each ROWS as [call, output, mono] (call)}
          <tr class="border-t border-line-1">
            <th scope="row" class="h-row px-3 font-mono font-normal whitespace-nowrap text-ink-2">
              {call}
            </th>
            <td class="h-row px-3 text-ink-1 tabular" class:font-mono={mono}>{output}</td>
            <td class="h-row px-3 font-mono text-caption whitespace-nowrap text-ink-3">
              {special(output)}
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
  <p class="font-mono text-caption break-all text-ink-3">
    hash = '{hash}' · at = new Date('{at.toISOString()}')
  </p>
</div>
