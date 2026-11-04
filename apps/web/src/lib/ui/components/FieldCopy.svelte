<script lang="ts">
  // The copy affordance of a read-only field. The tick holds for 1600 ms (design-system.md, Motion);
  // the hint says "Copied" for sight and a status line says it for assistive technology.
  import FieldButton from './FieldButton.svelte';
  import { fieldText } from './field-text';

  type Props = {
    value: string;
    label?: string;
    copiedLabel?: string;
  };

  let { value, label = fieldText.copy(), copiedLabel = fieldText.copied() }: Props = $props();

  const HOLD = 1600;

  let copied = $state(false);
  let timer: ReturnType<typeof setTimeout> | undefined;

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
    } catch {
      return; // The clipboard is blocked: report nothing.
    }
    copied = true;
    clearTimeout(timer);
    timer = setTimeout(() => (copied = false), HOLD);
  }

  $effect(() => () => clearTimeout(timer));
</script>

<FieldButton
  icon={copied ? 'check' : 'copy'}
  {label}
  hint={copied ? copiedLabel : undefined}
  onclick={copy}
/>
<span class="sr-only" role="status">{copied ? copiedLabel : ''}</span>
