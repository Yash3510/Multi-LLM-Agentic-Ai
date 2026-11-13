<script lang="ts">
  // The toasts (common look, Motion): top right, sliding down into place with a fade and fading
  // away; success in green, errors in red, each with a close button.
  import { fade, rise } from '$lib/ui/motion.svelte';
  import { dismiss, toasts } from '$lib/ui/toast.svelte';
  import Icon from '$lib/ui/icons/Icon.svelte';
</script>

<ol class="toaster" aria-live="polite">
  {#each toasts.list as one (one.id)}
    <li
      class="toast"
      data-kind={one.kind}
      role={one.kind === 'error' ? 'alert' : 'status'}
      in:rise={{ y: -8, duration: 400 }}
      out:fade={{ duration: 200 }}
    >
      <Icon
        name={one.kind === 'error' ? 'warning' : one.kind === 'info' ? 'info' : 'check'}
        size={16}
      />
      <span class="message">{one.message}</span>
      <button type="button" class="close" aria-label="Close" onclick={() => dismiss(one.id)}
        ><Icon name="x" size={12} /></button
      >
    </li>
  {/each}
</ol>

<style>
  .toaster {
    position: fixed;
    inset-block-start: 16px;
    inset-inline-end: 16px;
    z-index: 10000;
    display: flex;
    flex-direction: column;
    gap: 8px;
    inline-size: min(356px, calc(100vw - 32px));
    pointer-events: none;
  }

  .toast {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 14px 16px;
    border: 1px solid color-mix(in srgb, var(--color-ok-mark) 30%, transparent);
    border-radius: 8px;
    background-color: color-mix(in srgb, var(--color-ok-mark) 8%, var(--color-surface-raised));
    box-shadow: 0 4px 12px rgb(0 0 0 / 0.1);
    color: var(--color-ok);
    font-size: 13px;
    line-height: 18px;
    pointer-events: auto;
  }

  .toast[data-kind='error'] {
    border-color: color-mix(in srgb, var(--color-stop) 30%, transparent);
    background-color: color-mix(in srgb, var(--color-stop) 8%, var(--color-surface-raised));
    color: var(--color-stop);
  }

  .toast[data-kind='info'] {
    border-color: var(--color-line-1);
    background-color: var(--color-surface-raised);
    color: var(--color-ink-1);
  }

  .message {
    flex: 1;
    min-inline-size: 0;
  }

  .close {
    display: grid;
    flex-shrink: 0;
    place-items: center;
    inline-size: 20px;
    block-size: 20px;
    border-radius: var(--radius-pill);
    color: inherit;
    opacity: 0.6;
    transition: opacity 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  .close:hover {
    opacity: 1;
  }

  .close:focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: 1px;
  }
</style>
