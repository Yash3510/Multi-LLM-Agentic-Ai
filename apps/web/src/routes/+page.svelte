<script lang="ts">
  // New chat (chat-composer look §3.1-3.2): the top bar, then a centred column with the logomark,
  // the composer and the suggestions. Sending waits on the chat API (WP-RT-01); suggestions are
  // stand-ins until packs supply them.
  import { m } from '$lib/i18n/generated/messages.js';
  import Composer from '$lib/ui/components/Composer.svelte';
  import EgressIndicator from '$lib/ui/components/EgressIndicator.svelte';
  import IconButton from '$lib/ui/components/IconButton.svelte';
  import Logomark from '$lib/ui/components/Logomark.svelte';
  import TopBar from '$lib/ui/components/TopBar.svelte';
  import Icon from '$lib/ui/icons/Icon.svelte';

  const SUGGESTIONS = [
    { title: 'Check a threshold', detail: 'against R2 · Ratio' },
    { title: 'Audit sovereignty', detail: 'of this deployment' },
    { title: 'Draft an approval note', detail: 'for CASE-0142' },
  ];

  let draft = $state('');
</script>

<svelte:head><title>{m.app_name()}</title></svelte:head>

<TopBar>
  {#snippet end()}
    <IconButton icon="temporary-chat" label={m.shell_temporary_chat()} />
    <!-- Shows once the egress API answers a poll (own-4ce look S2). -->
    <EgressIndicator />
    <IconButton icon="controls" label={m.shell_controls()} />
  {/snippet}
</TopBar>

<div class="landing">
  <div class="welcome"><Logomark size={44} /></div>
  <div class="composer">
    <Composer bind:value={draft} model="Planner" tools={7} onsend={() => {}} />
  </div>
  <div class="suggestions">
    <p class="label"><Icon name="lightning" size={12} />{m.home_suggested()}</p>
    <ul>
      {#each SUGGESTIONS as suggestion (suggestion.title)}
        <li>
          <button type="button" class="card" onclick={() => (draft = suggestion.title)}>
            <span class="title">{suggestion.title}</span>
            <span class="detail">{suggestion.detail}</span>
          </button>
        </li>
      {/each}
    </ul>
  </div>
</div>

<style>
  .landing {
    display: flex;
    flex: 1;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    inline-size: 100%;
    max-inline-size: 928px;
    margin-inline: auto;
    /* 96 px each way, with the 6 px the running app gains above (its folder-title slot). */
    padding: 102px var(--spacing-1) 96px;
  }

  /* Gaps measured on the running app at the same window size. */
  .welcome {
    display: grid;
    place-items: center;
    margin-block-end: 40px;
  }

  .composer {
    inline-size: 100%;
    max-inline-size: 768px;
    padding: var(--spacing-3) var(--spacing-2);
  }

  .suggestions {
    inline-size: 100%;
    max-inline-size: 672px;
    margin-block-start: 22px;
    padding-inline: 20px;
  }

  .label {
    display: flex;
    align-items: center;
    gap: var(--spacing-1);
    margin-block-end: var(--spacing-1);
    color: var(--color-gray-600);
    font-size: var(--text-caption);
  }

  :global([data-theme='dark']) .label {
    color: var(--color-gray-400);
  }

  ul {
    display: flex;
    flex-direction: column;
  }

  .card {
    display: flex;
    flex-direction: column;
    inline-size: 100%;
    padding: 6px 10px;
    border-radius: 8px;
    text-align: start;
    line-height: 1.375;
    transition: color 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  .title {
    color: var(--color-ink-1);
    font-size: var(--text-ui);
  }

  .detail {
    color: var(--color-gray-600);
    font-size: var(--text-caption);
  }

  :global([data-theme='dark']) .detail {
    color: var(--color-gray-400);
  }

  .card:hover .title {
    color: var(--color-gray-950);
  }

  .card:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }
</style>
