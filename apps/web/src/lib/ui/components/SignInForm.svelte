<script lang="ts" module>
  export type SignInMode = 'sign-in' | 'sign-up' | 'first-account';
</script>

<script lang="ts">
  // The sign-in card (entry look E1): sign in, sign up and the first-account "get started" form.
  // It hands the values to its caller and never submits to a URL; the password stays in this
  // component's state only until the caller's call returns.
  import Icon from '$lib/ui/icons/Icon.svelte';
  import AuthField from './AuthField.svelte';

  type Props = {
    mode: SignInMode;
    product: string;
    onsubmit: (values: { name: string; email: string; password: string }) => Promise<void> | void;
    onswitch?: (mode: SignInMode) => void;
    /** Sign-up is offered by the server. */
    canSignUp?: boolean;
  };

  let { mode, product, onsubmit, onswitch, canSignUp = false }: Props = $props();

  let name = $state('');
  let email = $state('');
  let password = $state('');
  let error = $state('');
  let invalid = $state<'name' | 'email' | 'password' | undefined>();
  let caps = $state(false);
  let working = $state(false);

  const heading = $derived(
    {
      'sign-in': `Sign in to ${product}`,
      'sign-up': `Create your ${product} account`,
      'first-account': `Get started with ${product}`,
    }[mode],
  );
  const ACTION = {
    'sign-in': 'Sign in',
    'sign-up': 'Create account',
    'first-account': 'Create admin account',
  };
  const asksName = $derived(mode !== 'sign-in');

  const clear = () => {
    error = '';
    invalid = undefined;
  };

  async function submit(event: SubmitEvent) {
    event.preventDefault();
    if (working) return;
    const missing =
      asksName && !name.trim()
        ? 'name'
        : !email.trim()
          ? 'email'
          : !password
            ? 'password'
            : undefined;
    if (missing) {
      invalid = missing;
      error = {
        name: 'Enter your name.',
        email: 'Enter your email.',
        password: 'Enter your password.',
      }[missing];
      return;
    }
    working = true;
    try {
      await onsubmit({ name: name.trim(), email: email.trim(), password });
    } catch (failure) {
      error = failure instanceof Error ? failure.message : String(failure);
      invalid = 'password';
    } finally {
      working = false;
      password = '';
    }
  }
</script>

<div class="card">
  <h1 class="heading">{heading}</h1>
  {#if mode === 'first-account'}
    <p class="sub">The first account becomes the admin. Your data stays on this machine.</p>
  {/if}
  <form class="fields" novalidate onsubmit={submit}>
    {#if asksName}
      <AuthField
        label="Name"
        bind:value={name}
        autocomplete="name"
        invalid={invalid === 'name'}
        autofocus
        oninput={clear}
      />
    {/if}
    <AuthField
      label="Email"
      type="email"
      bind:value={email}
      autocomplete="email"
      invalid={invalid === 'email'}
      autofocus={!asksName}
      oninput={clear}
    />
    <AuthField
      label="Password"
      type="password"
      bind:value={password}
      autocomplete={mode === 'sign-in' ? 'current-password' : 'new-password'}
      invalid={invalid === 'password'}
      oninput={clear}
      onkeydown={(event) => (caps = event.getModifierState?.('CapsLock') ?? false)}
    />
    <!-- One collapsed block holding the Caps Lock and error rows, as in the running app. -->
    <div class="notes">
      <div class="note" data-open={caps && !error ? '' : undefined}>
        <div class="note-inner">
          <p class="caps"><Icon name="caps-lock" size={15} />Caps Lock is on</p>
        </div>
      </div>
      <div class="note" data-open={error ? '' : undefined}>
        <div class="note-inner">
          {#if error}
            <p class="error" role="alert"><Icon name="warning-circle" size={15} />{error}</p>
          {/if}
        </div>
      </div>
    </div>
    <button
      type="submit"
      class="primary"
      aria-busy={working}
      data-working={working ? '' : undefined}
    >
      <span class="layer label">{ACTION[mode]}</span>
      <span class="layer busy" aria-hidden="true">
        <svg viewBox="0 0 14 14" width="14" height="14">
          {#each [0, 1, 2, 3, 4, 5] as index (index)}
            <circle
              cx={7 + 5.2 * Math.sin((index * Math.PI) / 3)}
              cy={7 - 5.2 * Math.cos((index * Math.PI) / 3)}
              r="1.2"
              style:animation-delay="{[0, 0.28, 0.57, 0.85, 1.13, 1.42][index]}s"
            />
          {/each}
          <circle class="hub" cx="7" cy="7" r="1" />
        </svg>
        {mode === 'sign-in' ? 'Signing in' : 'Creating your account'}
      </span>
    </button>
  </form>
  {#if mode === 'sign-in'}
    <p class="forgot">Forgot your password? Your admin can reset it.</p>
  {/if}
  {#if canSignUp && mode !== 'first-account'}
    <p class="switch">
      {mode === 'sign-in' ? 'New here?' : 'Already have an account?'}
      <button
        type="button"
        class="link"
        onclick={() => onswitch?.(mode === 'sign-in' ? 'sign-up' : 'sign-in')}
      >
        {mode === 'sign-in' ? 'Create an account' : 'Sign in'}
      </button>
    </p>
  {/if}
</div>

<style>
  .card {
    inline-size: 100%;
    max-inline-size: 344px;
    margin: auto;
    padding-block-end: 40px;
    text-align: start;
  }

  .heading {
    margin-block-end: var(--spacing-6);
    color: var(--color-gray-900);
    font-size: 26px;
    font-weight: var(--font-weight-medium);
    letter-spacing: -0.01em;
    line-height: 1.25;
  }

  :global([data-theme='dark']) .heading {
    color: var(--color-gray-50);
  }

  .sub {
    margin: -12px 0 20px;
    color: var(--color-gray-600);
    font-size: var(--text-small);
    line-height: 1.625;
  }

  .fields {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .note {
    display: grid;
    grid-template-rows: 0fr;
    opacity: 0;
    transition:
      grid-template-rows 300ms cubic-bezier(0.22, 1, 0.36, 1),
      opacity 220ms ease;
  }

  .note[data-open] {
    grid-template-rows: 1fr;
    opacity: 1;
  }

  .note-inner {
    overflow: hidden;
  }

  .error,
  .caps {
    display: flex;
    gap: 6px;
    padding-block-start: 10px;
    font-size: 12.5px;
  }

  .error {
    align-items: flex-start;
    color: var(--color-red-700);
    line-height: 1.375;
  }

  .error :global(svg) {
    translate: 0 1px;
  }

  .caps {
    align-items: center;
    color: var(--color-gray-600);
  }

  :global([data-theme='dark']) .error {
    color: var(--color-red-300);
  }

  :global([data-theme='dark']) .caps {
    color: var(--color-gray-400);
  }

  .primary {
    position: relative;
    inline-size: 100%;
    block-size: 46px;
    margin-block-start: var(--spacing-4);
    overflow: hidden;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-900);
    color: var(--color-white);
    font-size: 14.5px;
    font-weight: var(--font-weight-medium);
    transition:
      background-color 150ms,
      transform 150ms;
  }

  .primary:hover {
    background-color: var(--color-gray-800);
  }

  .primary:active {
    transform: scale(0.99);
  }

  .primary[data-working] {
    cursor: default;
  }

  :global([data-theme='dark']) .primary {
    background-color: var(--color-white);
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .primary:hover {
    background-color: var(--color-gray-100);
  }

  .primary:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .layer {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-2);
    transition:
      opacity 280ms ease,
      translate 400ms cubic-bezier(0.22, 1, 0.36, 1);
  }

  .busy {
    opacity: 0;
    translate: 0 6px;
  }

  .primary[data-working] .label {
    opacity: 0;
    translate: 0 -6px;
  }

  .primary[data-working] .busy {
    opacity: 1;
    translate: 0 0;
  }

  .busy circle {
    fill: var(--color-violet-300);
    opacity: 0.35;
    animation: lap 1.7s ease-in-out infinite;
  }

  .busy circle.hub {
    opacity: 1;
    animation: none;
  }

  :global([data-theme='dark']) .busy circle {
    fill: var(--color-violet-600);
  }

  .forgot {
    margin-block-start: var(--spacing-3);
    line-height: 1.5;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    text-align: center;
  }

  :global([data-theme='dark']) .forgot {
    color: var(--color-gray-400);
  }

  .switch {
    margin-block-start: 20px;
    color: var(--color-gray-600);
    font-size: var(--text-small);
    text-align: center;
  }

  .link {
    color: var(--color-gray-900);
    text-decoration: underline;
    text-decoration-color: var(--color-gray-300);
    text-underline-offset: 3px;
    transition: text-decoration-color 200ms ease;
  }

  .link:hover {
    text-decoration-color: currentColor;
  }

  @keyframes lap {
    0% {
      opacity: 1;
    }
    35% {
      opacity: 0.7;
    }
    70%,
    100% {
      opacity: 0.35;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .note,
    .layer {
      transition: none;
    }

    .busy circle {
      animation: none;
      opacity: 0.8;
    }
  }
</style>
