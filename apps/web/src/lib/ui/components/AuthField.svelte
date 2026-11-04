<script lang="ts">
  // The sign-in text field (entry look E2): a 52 px field whose label floats up when the field is
  // focused, filled or autofilled; password fields add a show/hide button that keeps focus.
  import Icon from '$lib/ui/icons/Icon.svelte';

  type Props = {
    label: string;
    type?: 'text' | 'email' | 'password';
    value?: string;
    autocomplete?: HTMLInputElement['autocomplete'];
    invalid?: boolean;
    autofocus?: boolean;
    oninput?: () => void;
    onkeydown?: (event: KeyboardEvent) => void;
  };

  let {
    label,
    type = 'text',
    value = $bindable(''),
    autocomplete,
    invalid = false,
    autofocus = false,
    oninput,
    onkeydown,
  }: Props = $props();

  const id = $props.id();
  let shown = $state(false);
  let input: HTMLInputElement | undefined = $state();
  const inputType = $derived(type === 'password' && shown ? 'text' : type);

  // Focus once the page has laid out, as the running app's sign-in does for its first field.
  $effect(() => {
    if (!autofocus || !input) return;
    const field = input;
    const frame = requestAnimationFrame(() => field.focus({ preventScroll: true }));
    return () => cancelAnimationFrame(frame);
  });
</script>

<div class="field" data-password={type === 'password' ? '' : undefined}>
  <input
    bind:this={input}
    {id}
    class="control"
    type={inputType}
    bind:value
    {autocomplete}
    aria-invalid={invalid}
    placeholder=" "
    spellcheck="false"
    {oninput}
    {onkeydown}
  />
  <label class="label" for={id}>{label}</label>
  {#if type === 'password'}
    <button
      type="button"
      class="eye"
      aria-label={shown ? 'Hide password' : 'Show password'}
      onmousedown={(event) => event.preventDefault()}
      onclick={() => (shown = !shown)}
    >
      <Icon name={shown ? 'eye-slash' : 'eye'} size={18} />
    </button>
  {/if}
</div>

<style>
  .field {
    position: relative;
    inline-size: 100%;
  }

  .control {
    inline-size: 100%;
    block-size: 52px;
    padding: 20px 14px 6px;
    border: 1px solid var(--color-gray-200);
    border-radius: 16px;
    background-color: color-mix(in srgb, var(--color-gray-50) 70%, transparent);
    caret-color: var(--color-gray-900);
    color: var(--color-gray-900);
    font-size: var(--text-body);
    line-height: 1.5;
    outline: none;
    transition:
      border-color 200ms,
      background-color 200ms,
      box-shadow 200ms;
  }

  .field[data-password] .control {
    padding-inline-end: 48px;
  }

  .control:focus {
    border-color: var(--color-gray-900);
    background-color: var(--color-white);
    box-shadow: 0 0 0 4px rgb(22 22 22 / 0.06);
  }

  .control[aria-invalid='true'] {
    border-color: var(--color-red-300);
  }

  .control[aria-invalid='true']:focus {
    border-color: var(--color-red-400);
    box-shadow: 0 0 0 4px rgb(248 113 113 / 0.15);
  }

  :global([data-theme='dark']) .control {
    color-scheme: dark;
    border-color: var(--color-gray-800);
    background-color: color-mix(in srgb, var(--color-gray-900) 60%, transparent);
    caret-color: var(--color-white);
    color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .control:focus {
    border-color: var(--color-gray-300);
    background-color: var(--color-gray-900);
    box-shadow: 0 0 0 4px rgb(255 255 255 / 0.07);
  }

  :global([data-theme='dark']) .control[aria-invalid='true'] {
    border-color: color-mix(in srgb, var(--color-red-400) 50%, transparent);
  }

  /* Autofill keeps the field's own fill (E2). */
  .control:-webkit-autofill {
    -webkit-text-fill-color: var(--color-gray-900);
    transition: background-color 600000s;
  }

  .label {
    position: absolute;
    inset-block-start: 15px;
    inset-inline-start: 15px;
    color: var(--color-gray-500);
    font-size: var(--text-body);
    line-height: 1.4;
    pointer-events: none;
    transform-origin: top left;
    transition:
      transform 200ms cubic-bezier(0.22, 1, 0.36, 1),
      color 200ms ease;
  }

  .control:is(:focus, :not(:placeholder-shown), :-webkit-autofill) + .label {
    transform: translateY(-9px) scale(0.76);
    color: var(--color-gray-600);
  }

  :global([data-theme='dark']) .control:is(:focus, :not(:placeholder-shown)) + .label {
    color: var(--color-gray-400);
  }

  .eye {
    position: absolute;
    inset-block-start: 9px;
    inset-inline-end: 8px;
    display: grid;
    place-items: center;
    inline-size: 34px;
    block-size: 34px;
    border-radius: var(--radius-inset);
    color: var(--color-gray-500);
    transition:
      color 150ms,
      background-color 150ms;
  }

  .eye:hover {
    background-color: rgb(22 22 22 / 0.05);
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .eye {
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) .eye:hover {
    background-color: rgb(255 255 255 / 0.07);
    color: var(--color-white);
  }

  .eye:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }
</style>
