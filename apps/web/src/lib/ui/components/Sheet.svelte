<script lang="ts">
  // A modal sheet docked to the bottom edge: a dialog whose panel spans the width (up to 960 px)
  // with only its top corners rounded, for pickers and short forms that want the room, mostly on a
  // tablet. Same behaviour as Dialog: focus held and returned, Esc closes, an optional scrim press.
  import type { ComponentProps } from 'svelte';
  import Dialog from './Dialog.svelte';

  type Props = Omit<ComponentProps<typeof Dialog>, 'placement' | 'size'>;

  let { open = $bindable(false), ...rest }: Props = $props();
</script>

<Dialog bind:open placement="bottom" {...rest} />
