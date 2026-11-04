<script lang="ts">
  // A conversation at /c/[id], as the running app addresses it (chat-composer look §1.3, chat-messages look §1-3): the top bar with the title,
  // the thread from 72 px down, and the composer at the bottom. The chat comes from the data
  // source (web-data-contract.md).
  import { m } from '$lib/i18n/generated/messages.js';
  import Composer from '$lib/ui/components/Composer.svelte';
  import EgressIndicator from '$lib/ui/components/EgressIndicator.svelte';
  import IconButton from '$lib/ui/components/IconButton.svelte';
  import ResponseMessage from '$lib/ui/components/ResponseMessage.svelte';
  import TopBar from '$lib/ui/components/TopBar.svelte';
  import UserMessage from '$lib/ui/components/UserMessage.svelte';

  import type { PageProps } from './$types';

  let { data }: PageProps = $props();

  const chat = $derived(data.chat);
  const messages = $derived(chat.messages);
  const lastResponse = $derived(messages.findLastIndex((message) => message.role === 'response'));
</script>

<svelte:head><title>{chat ? `${chat.title} / ${m.app_name()}` : m.app_name()}</title></svelte:head>

<div class="chat">
  <TopBar title={chat?.title} onchatactions={() => {}}>
    {#snippet end()}
      <EgressIndicator />
      <IconButton icon="controls" label={m.shell_controls()} />
    {/snippet}
  </TopBar>

  <div class="thread">
    {#each messages as message, index (index)}
      {#if message.role === 'user'}
        <UserMessage text={message.text} at={message.at} />
      {:else}
        <ResponseMessage
          model="4CE / Planner"
          status={message.direct?.status}
          direct={message.direct}
          text={message.text}
          at={message.at}
          last={index === lastResponse}
        />
      {/if}
    {/each}
  </div>

  <div class="composer">
    <div class="inner">
      <Composer
        model="Planner"
        tools={7}
        onsend={() => {}}
        placeholder={m.composer_reply_placeholder()}
      />
    </div>
  </div>
</div>

<style>
  .chat {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-block-size: 0;
  }

  .thread {
    flex: auto;
    /* 72 px to clear the floating bar, plus the 9 px the running app's first row sits lower. */
    padding-block: 81px 10px;
    margin-block-start: -48px;
  }

  .composer {
    position: sticky;
    inset-block-end: 0;
    z-index: 10;
    display: flex;
    justify-content: center;
    /* 8 px block padding, the 2 px footer spacer and the empty disclaimer line: 22 px measured. */
    padding: 0 var(--spacing-2) 22px;
    background: linear-gradient(to top, var(--color-surface-page) 60%, transparent);
  }

  .inner {
    inline-size: 100%;
    max-inline-size: 928px;
  }
</style>
