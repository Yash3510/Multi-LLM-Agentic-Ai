<script lang="ts">
  // A conversation at /c/[id], as the running app addresses it (chat-composer look §1.3,
  // chat-messages look §1-3): the top bar with the title, the thread from 72 px down, and the
  // composer at the bottom. Sending streams the answer from the data source
  // (web-data-contract.md); Stop aborts it.
  import { data as source, type Message } from '$lib/data';
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
  // The thread as shown: the stored messages plus anything asked here. Reset on another chat.
  let messages = $state<Message[]>([]);
  let controller = $state<AbortController | undefined>();
  $effect.pre(() => {
    messages = [...data.chat.messages];
    return () => controller?.abort();
  });

  async function ask(question: string) {
    const now = new Date();
    messages.push({ id: `u-${now.getTime()}`, role: 'user', text: question, at: now });
    messages.push({
      id: `r-${now.getTime()}`,
      role: 'response',
      text: '',
      at: now,
      events: [],
      finished: false,
    });
    // The pushed object is proxied; read it back so updates reach the screen.
    const answer = messages[messages.length - 1];
    controller = new AbortController();
    const { signal } = controller;
    try {
      for await (const event of source.ask(chat.id, question, signal)) {
        answer.events?.push(event);
        if (event.type === 'delta') answer.text += event.text;
        if (event.type === 'done' || event.type === 'error') answer.finished = true;
      }
    } finally {
      if (signal.aborted) {
        answer.events?.push({ type: 'stopped', at: Date.now() });
        answer.finished = true;
      }
      controller = undefined;
    }
  }
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
          events={message.events}
          finished={message.finished}
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
        onsend={ask}
        busy={controller !== undefined}
        onstop={() => controller?.abort()}
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
