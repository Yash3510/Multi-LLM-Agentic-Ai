<script lang="ts">
  // Every icon by name: Lucide glyphs listed in registry.json (ADR-0041 amendment), drawn at a
  // 1.75 stroke with round caps and joins. Colour is currentColor, so it comes from the wrapper.
  import { ICONS, type IconName } from './generated/icons';

  type Props = {
    name: IconName;
    /** In CSS pixels. */
    size?: number;
    /** Gives the icon role="img" and this accessible name; leave it out when text says the same. */
    label?: string;
  };

  let { name, size = 20, label }: Props = $props();
</script>

<svg
  viewBox="0 0 24 24"
  width={size}
  height={size}
  fill="none"
  stroke="currentColor"
  stroke-width="1.75"
  stroke-linecap="round"
  stroke-linejoin="round"
  role={label ? 'img' : undefined}
  aria-label={label}
  aria-hidden={label ? undefined : true}
>
  {#each ICONS[name] as [tag, geometry], index (index)}
    <svelte:element this={tag} {...geometry} />
  {/each}
</svg>

<style>
  svg {
    flex-shrink: 0;
  }
</style>
