<script lang="ts">
  // The workspace switch (workspace look §0.7): a 28 by 16 track with a 12 px thumb, named for its
  // state ("Enabled" or "Disabled").
  type Props = {
    on: boolean;
    onchange: (on: boolean) => void;
    /** The switch's name when a visible label sits beside it; otherwise it is named by state. */
    label?: string;
  };

  let { on, onchange, label }: Props = $props();
</script>

<button
  type="button"
  class="switch"
  role="switch"
  aria-checked={on}
  aria-label={label ?? (on ? 'Enabled' : 'Disabled')}
  title={on ? 'Enabled' : 'Disabled'}
  data-on={on ? '' : undefined}
  onclick={() => onchange(!on)}><span class="thumb"></span></button
>

<style>
  .switch {
    position: relative;
    inline-size: 28px;
    block-size: 16px;
    margin-inline: 1px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-300);
    transition: background-color 150ms;
  }

  .switch[data-on] {
    background-color: var(--color-gray-900);
  }

  .thumb {
    position: absolute;
    inset-block-start: 2px;
    inset-inline-start: 2px;
    inline-size: 12px;
    block-size: 12px;
    border-radius: var(--radius-pill);
    background-color: var(--color-white);
    transition: inset-inline-start 150ms;
  }

  .switch[data-on] .thumb {
    inset-inline-start: 14px;
  }

  :global([data-theme='dark']) .switch {
    background-color: var(--color-gray-700);
  }

  :global([data-theme='dark']) .switch .thumb {
    background-color: var(--color-gray-500);
  }

  :global([data-theme='dark']) .switch[data-on] {
    background-color: var(--color-white);
  }

  :global([data-theme='dark']) .switch[data-on] .thumb {
    background-color: var(--color-black);
  }

  .switch:focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
