<script lang="ts">
  // The sign-in page (entry look E1): the ground, the corner mark at 40 px and the sign-in card.
  // A server with no account yet shows the first-account form instead.
  import { goto } from '$app/navigation';
  import { resolve } from '$app/paths';
  import { data } from '$lib/data';
  import { m } from '$lib/i18n/generated/messages.js';
  import Logomark from '$lib/ui/components/Logomark.svelte';
  import SignInForm, { type SignInMode } from '$lib/ui/components/SignInForm.svelte';

  let mode = $state<SignInMode>('sign-in');

  $effect(() => {
    void data.setupStatus().then(({ firstAccount }) => {
      if (firstAccount) mode = 'first-account';
    });
  });

  async function submit({
    name,
    email,
    password,
  }: {
    name: string;
    email: string;
    password: string;
  }) {
    if (mode === 'first-account') await data.createFirstAccount(name, email, password);
    else if (mode === 'sign-up') await data.signUp(name, email, password);
    else await data.signIn(email, password);
    await goto(resolve('/'), { invalidateAll: true });
  }
</script>

<svelte:head><title>{m.app_name()}</title></svelte:head>

<div class="page">
  <span class="corner"><Logomark size={24} /></span>
  <main class="column">
    <SignInForm
      {mode}
      product={m.app_name()}
      onsubmit={submit}
      onswitch={(next) => (mode = next)}
    />
  </main>
</div>

<style>
  .page {
    position: relative;
    min-block-size: 100dvh;
    background-color: var(--color-white);
    color: var(--color-black);
  }

  :global([data-theme='dark']) .page {
    background-color: var(--color-black);
    color: var(--color-white);
  }

  .corner {
    position: fixed;
    inset-block-start: 40px;
    inset-inline-start: 40px;
    z-index: 50;
    display: inline-flex;
  }

  .column {
    display: flex;
    flex-direction: column;
    min-block-size: 100dvh;
    padding-inline: 40px;
  }
</style>
