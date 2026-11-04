<script lang="ts">
  // Every icon by name: Phosphor glyphs listed in registry.json, in the weight the running app uses
  // in that place (ADR-0041 amendment). One filled path on the 256 grid; colour is currentColor,
  // so it comes from the wrapper.
  import { ICONS, type IconName } from './generated/icons';

  type Props = {
    name: IconName;
    /** In CSS pixels: 16 in rows and menus, 18 in the sidebar and top bar. */
    size?: number;
    /** Gives the icon role="img" and this accessible name; leave it out when text says the same. */
    label?: string;
  };

  let { name, size = 16, label }: Props = $props();
</script>

<svg
  viewBox="0 0 256 256"
  width={size}
  height={size}
  fill="currentColor"
  role={label ? 'img' : undefined}
  aria-label={label}
  aria-hidden={label ? undefined : true}
>
  <path d={ICONS[name]} />
</svg>

<style>
  svg {
    flex-shrink: 0;
  }
</style>
