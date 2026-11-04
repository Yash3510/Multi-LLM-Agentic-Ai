<script module lang="ts">
  import type { IconName } from '$lib/ui/icons/generated/icons';

  export type AlertTone = 'info' | 'caution' | 'stop';

  // Class names are written out in full so Tailwind finds them. Info is neutral: violet is kept for
  // live work and focus, and green means PASS, so neither tells the reader something general.
  // The measured notice line (chat-messages look §2.8): a 3% tint (4% in dark), muted text; caution
  // and stop keep that frame on their 20% fills.
  const TONES: Record<AlertTone, { icon: IconName; box: string; mark: string }> = {
    info: {
      icon: 'info',
      box: 'bg-track text-ink-2',
      mark: 'text-ink-3',
    },
    caution: { icon: 'warning', box: 'bg-caution-soft text-caution', mark: 'text-caution-mark' },
    stop: { icon: 'stop', box: 'bg-stop-soft text-stop', mark: 'text-stop-mark' },
  };
</script>

<script lang="ts">
  // A message inside the flow: icon plus text, never colour alone. Its action sits in a row under
  // the text, aligned with it. Stop is an alert, announced at once; info and caution are polite
  // status messages. Errors also show here, in place, beside what they are about.
  import type { Snippet } from 'svelte';
  import Icon from '$lib/ui/icons/Icon.svelte';

  type Props = {
    tone?: AlertTone;
    /** A short first line in medium weight. */
    title?: string;
    children: Snippet;
    /** The way forward, named by verb and object, e.g. a "Retry saving" button. */
    action?: Snippet;
    /** Replaces the tone's glyph, e.g. unverified for "could not check". */
    icon?: IconName;
    /** The text's language when it differs from the page's. */
    lang?: string;
  };

  let { tone = 'info', title, children, action, icon, lang }: Props = $props();

  const look = $derived(TONES[tone]);
</script>

<div
  class="flex items-start gap-2.5 rounded-notice px-3 py-2.5 text-small {look.box}"
  role={tone === 'stop' ? 'alert' : 'status'}
  {lang}
>
  <span class="glyph inline-flex shrink-0 items-center {look.mark}">
    <Icon name={icon ?? look.icon} size={16} />
  </span>
  <div class="flex min-w-0 flex-1 flex-col gap-2 break-words">
    <div class="flex flex-col">
      {#if title}
        <p class="font-medium">{title}</p>
      {/if}
      <div>{@render children()}</div>
    </div>
    {#if action}
      <div class="flex flex-wrap items-center gap-2">{@render action()}</div>
    {/if}
  </div>
</div>

<style>
  /* The glyph sits on the first line of text, whatever size that text inherits from its density. */
  .glyph {
    height: 1lh;
  }
</style>
