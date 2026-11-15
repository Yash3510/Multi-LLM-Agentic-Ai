<script lang="ts">
  // The toasts: top right, sliding down into place with a fade and fading away. One quiet glass
  // surface for every kind; the icon alone carries the colour (green done, red failed, ink note).
  // A toast waits while the pointer or focus is on it.
  import { fade, rise } from '$lib/ui/motion.svelte';
  import { dismiss, hold, release, toasts } from '$lib/ui/toast.svelte';
  import Icon from '$lib/ui/icons/Icon.svelte';
</script>

<ol class="toaster" aria-live="polite">
  {#each toasts.list as one (one.id)}
    <li
      class="toast glass"
      data-kind={one.kind}
      role={one.kind === 'error' ? 'alert' : 'status'}
      in:rise={{ y: -8, duration: 400 }}
      out:fade={{ duration: 200 }}
      onpointerenter={() => hold(one.id)}
      onpointerleave={() => release(one.id)}
      onfocusin={() => hold(one.id)}
      onfocusout={() => release(one.id)}
    >
      <span class="sign"
        ><Icon
          name={one.kind === 'error' ? 'warning' : one.kind === 'info' ? 'info' : 'verdict-pass'}
          size={18}
        /></span
      >
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
    align-items: flex-start;
    gap: 10px;
    padding: 12px 10px 12px 14px;
    border: 1px solid var(--color-line-1);
    border-radius: var(--radius-notice);
    box-shadow: var(--shadow-e2), var(--glass-edge);
    color: var(--color-ink-1);
    font-size: 13px;
    line-height: 20px;
    pointer-events: auto;
  }

  /* One line of text tall, so the icon sits on the first line of a wrapped message. */
  .sign {
    display: grid;
    flex-shrink: 0;
    place-items: center;
    block-size: 20px;
    color: var(--color-ok);
  }

  .toast[data-kind='error'] .sign {
    color: var(--color-stop);
  }

  .toast[data-kind='info'] .sign {
    color: var(--color-ink-2);
  }

  .message {
    flex: 1;
    min-inline-size: 0;
    overflow-wrap: anywhere;
  }

  .close {
    display: grid;
    flex-shrink: 0;
    place-items: center;
    inline-size: 20px;
    block-size: 20px;
    border-radius: var(--radius-pill);
    color: var(--color-ink-3);
    transition:
      color var(--duration-interact) var(--ease-standard),
      background-color var(--duration-interact) var(--ease-standard);
  }

  .close:hover {
    background-color: var(--color-tint);
    color: var(--color-ink-1);
  }

  .close:focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: 1px;
  }
</style>
