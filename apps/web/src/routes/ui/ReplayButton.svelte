<script lang="ts">
  // A quiet icon button that replays one demo. The label is the accessible name; the icon says it.
  import Icon from '$lib/ui/icons/Icon.svelte';

  let { label, onclick }: { label: string; onclick: () => void } = $props();
</script>

<button
  type="button"
  class="inline-flex size-6 shrink-0 items-center justify-center rounded-control border border-transparent text-ink-2 transition-colors duration-quick hover:border-line-2 hover:bg-surface-hover hover:text-ink-1"
  aria-label={label}
  {onclick}
>
  <Icon name="arrow-clockwise" size={16} />
</button>
