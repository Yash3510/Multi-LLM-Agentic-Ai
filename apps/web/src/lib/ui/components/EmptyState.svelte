<script lang="ts">
  // Nothing to show yet: a static icon, a one-line title, one line saying what was checked, and at
  // most one action. The icon never moves; an empty state is not a state change seen live.
  import type { Snippet } from 'svelte';
  import type { IconName } from '$lib/ui/icons/generated/icons';
  import Icon from '$lib/ui/icons/Icon.svelte';

  type Props = {
    /** A Lucide glyph from the registry. */
    icon: IconName;
    title: string;
    /** What was checked, so empty reads as a result, not a fault. */
    detail: string;
    /** The one action, e.g. a button. */
    action?: Snippet;
    /** The text's language when it differs from the page's. */
    lang?: string;
  };

  let { icon, title, detail, action, lang }: Props = $props();
</script>

<div class="flex flex-col items-center gap-4 px-6 py-8 text-center" {lang}>
  <span class="inline-flex text-ink-3"><Icon name={icon} size={32} /></span>
  <div class="flex max-w-prose flex-col gap-1">
    <p class="text-ui font-medium text-balance text-ink-1">{title}</p>
    <p class="text-small text-balance text-ink-2">{detail}</p>
  </div>
  {#if action}
    <div class="flex">{@render action()}</div>
  {/if}
</div>
