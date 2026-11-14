<script lang="ts">
  // New chat (chat-composer look §3.1-3.2): the top bar, then a centred column with the logomark,
  // the composer, and the suggestions beside the newest chats. Sending waits on the chat API
  // (WP-RT-01); suggestions are stand-ins until packs supply them.
  import { resolve } from '$app/paths';
  import { m } from '$lib/i18n/generated/messages.js';
  import { getLocale } from '$lib/i18n/generated/runtime.js';
  import Composer from '$lib/ui/components/Composer.svelte';
  import EgressIndicator from '$lib/ui/components/EgressIndicator.svelte';
  import IconButton from '$lib/ui/components/IconButton.svelte';
  import Logomark from '$lib/ui/components/Logomark.svelte';
  import TopBar from '$lib/ui/components/TopBar.svelte';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { longDate } from '$lib/ui/ago';
  import { formatAgo, toIntlLocale } from '$lib/ui/format';
  import { fade } from '$lib/ui/motion.svelte';
  import type { LayoutData } from './$types';

  const SUGGESTIONS = [
    { title: 'Check a threshold', detail: 'against R2 · Ratio' },
    { title: 'Audit sovereignty', detail: 'of this deployment' },
    { title: 'Draft an approval note', detail: 'for CASE-0142' },
  ];

  let { data }: { data: LayoutData } = $props();

  const locale = toIntlLocale(getLocale());

  // The layout lists chats newest first.
  const recent = $derived(data.chats.slice(0, 3));

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
  <!-- The logo, then the suggestions, fade in as on the running app (common look, Motion). -->
  <div class="welcome" data-mark-turn in:fade={{ duration: 200 }}><Logomark size={44} /></div>
  <div class="composer">
    <Composer
      bind:value={draft}
      model="Planner"
      tools={7}
      suggestion={`${SUGGESTIONS[0].title} ${SUGGESTIONS[0].detail}`}
      onsend={() => {}}
    />
  </div>
  <div class="columns" in:fade={{ duration: 200, delay: 200 }}>
    <div>
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
    {#if recent.length}
      <div>
        <p class="label">{m.home_recent()}</p>
        <ul>
          {#each recent as chat (chat.id)}
            <li>
              <a class="card recent" href={resolve('/c/[id]', { id: chat.id })}>
                <span class="title">{chat.title}</span>
                <time datetime={chat.updated.toISOString()} title={longDate.format(chat.updated)}>
                  {formatAgo(chat.updated, { locale })}
                </time>
              </a>
            </li>
          {/each}
        </ul>
      </div>
    {/if}
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

  .columns {
    display: grid;
    gap: 22px 28px;
    inline-size: 100%;
    max-inline-size: 672px;
    margin-block-start: 26px;
    padding-inline: 20px;
  }

  @media (min-width: 40rem) {
    .columns {
      grid-auto-columns: minmax(0, 1fr);
      grid-auto-flow: column;
    }
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
    padding: 9px 2px;
    text-align: start;
    line-height: 1.375;
    transition: color 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  li + li {
    border-block-start: 1px solid var(--color-line-1);
  }

  .title {
    color: var(--color-ink-1);
    font-size: var(--text-ui);
  }

  /* A recent chat: its title on one line, its age at the end. */
  .recent {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: baseline;
    gap: var(--spacing-3);
  }

  .recent .title {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  time {
    color: var(--color-ink-3);
    font-family: var(--font-mono);
    font-size: 11px;
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
