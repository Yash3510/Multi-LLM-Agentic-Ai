<script lang="ts">
  // A conversation at /c/[id], as the running app addresses it (chat-composer look §1.3,
  // chat-messages look §1-3): the top bar with the title, the thread from 72 px down, and the
  // composer at the bottom. Sending starts a run and follows it (web-data-contract.md): Stop
  // cancels the run, leaving the chat only stops following, and a dropped connection resumes.
  import { data as source, type Message } from '$lib/data';
  import { ends, watchRun } from '$lib/data/runs';
  import { m } from '$lib/i18n/generated/messages.js';
  import Composer from '$lib/ui/components/Composer.svelte';
  import EgressIndicator from '$lib/ui/components/EgressIndicator.svelte';
  import IconButton from '$lib/ui/components/IconButton.svelte';
  import ResponseMessage from '$lib/ui/components/ResponseMessage.svelte';
  import SignOffPanel from '$lib/ui/components/SignOffPanel.svelte';
  import TopBar from '$lib/ui/components/TopBar.svelte';
  import UserMessage from '$lib/ui/components/UserMessage.svelte';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { nearBottom } from '$lib/ui/follow';
  import { onMount, tick, untrack } from 'svelte';

  import type { PageProps } from './$types';

  let { data }: PageProps = $props();

  const chat = $derived(data.chat);
  // The thread as shown: the stored messages plus anything asked here. Reset on another chat.
  let messages = $state<Message[]>([]);
  let controller = $state<AbortController | undefined>();
  // The followed answer's dropped connection is being re-established.
  let reconnecting = $state(false);
  $effect.pre(() => {
    messages = [...data.chat.messages];
    // An answer still running when the chat opens again picks up after its last event.
    untrack(() => {
      const last = messages.at(-1);
      if (last?.role === 'response' && last.runId && !last.finished)
        void follow(last, last.runId, last.events?.at(-1)?.seq ?? 0);
    });
    return () => controller?.abort();
  });

  // The answer waiting for the person: its sign-off request arrived and no decision yet.
  const waiting = $derived.by(() => {
    const answer = messages.at(-1);
    const events = answer?.role === 'response' ? (answer.events ?? []) : [];
    const request = events.findLast((event) => event.type === 'sign-off');
    if (!answer || !request || events.some((event) => event.type === 'decision')) return undefined;
    const sources = events.flatMap((event) => (event.type === 'source' ? [event.source] : []));
    return { answer, request: request.request, sources };
  });

  // Follow the newest text while the reader is at the end of the thread.
  let scroller: HTMLElement | null = null;
  let following = $state(true);
  const toBottom = () => scroller?.scrollTo({ top: scroller.scrollHeight });

  onMount(() => {
    scroller = document.getElementById('main');
    if (!scroller) return;
    const element = scroller;
    const onScroll = () => (following = nearBottom(element));
    element.addEventListener('scroll', onScroll, { passive: true });
    toBottom();
    return () => element.removeEventListener('scroll', onScroll);
  });

  // Every change to the last message (text, events) keeps the end in view while following.
  $effect(() => {
    const last = messages.at(-1);
    void last?.text;
    void last?.events?.length;
    if (following) void tick().then(() => toBottom());
  });

  // Follows the answer's run to its end, through the sign-off and any dropped connection.
  async function follow(answer: Message, runId: string, after = 0) {
    const following = new AbortController();
    controller = following;
    try {
      const onreconnecting = (state: boolean) => (reconnecting = state);
      const watch = watchRun(source, runId, after, { signal: following.signal, onreconnecting });
      for await (const event of watch) {
        answer.events?.push(event);
        if (event.type === 'delta') answer.text += event.text;
        if (ends(event)) answer.finished = true;
      }
    } finally {
      if (controller === following) controller = undefined;
    }
  }

  // The run goes on to its decision, receipt and end on the follow already open.
  function decide(outcome: 'released' | 'withheld', reason?: string) {
    const runId = waiting?.answer.runId;
    if (runId) void source.decide(runId, outcome, reason);
  }

  function stop() {
    const runId = messages.at(-1)?.runId;
    if (runId) void source.cancelRun(runId);
  }

  // Try again: the stopped answer goes and its question runs again.
  async function retry() {
    const question = messages.findLast((message) => message.role === 'user')?.text;
    if (!question || messages.at(-1)?.role !== 'response') return;
    messages.pop();
    messages.pop();
    await ask(question);
  }

  async function ask(question: string) {
    const now = new Date();
    following = true;
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
    answer.runId = await source.ask(chat.id, question);
    await follow(answer, answer.runId);
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
        <UserMessage
          text={message.text}
          at={message.at}
          fresh={index >= data.chat.messages.length}
        />
      {:else}
        <ResponseMessage
          model="4CE / Planner"
          status={message.direct?.status}
          direct={message.direct}
          events={message.events}
          finished={message.finished}
          runId={message.runId}
          reconnecting={index === lastResponse && reconnecting}
          text={message.text}
          at={message.at}
          last={index === lastResponse}
          onretry={retry}
        />
      {/if}
    {/each}
  </div>

  <div class="composer">
    {#if !following}
      <!-- Scroll-to-bottom (chat-composer look §4.1): 48 px above the composer, round. -->
      <div class="to-bottom">
        <button
          type="button"
          aria-label={m.chat_scroll_bottom()}
          title={m.chat_scroll_bottom()}
          onclick={() => {
            following = true;
            toBottom();
          }}
        >
          <Icon name="arrow-down" size={20} />
        </button>
      </div>
    {/if}
    <div class="inner">
      {#if waiting}
        <SignOffPanel
          request={waiting.request}
          draft={waiting.answer.text}
          sources={waiting.sources}
          model="qwen/qwen3-8b"
          ondecide={decide}
        />
      {:else}
        <Composer
          model="Planner"
          tools={7}
          onsend={ask}
          busy={controller !== undefined}
          onstop={stop}
          placeholder={m.composer_reply_placeholder()}
        />
      {/if}
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

  .to-bottom {
    position: absolute;
    inset-block-start: -48px;
    inset-inline: 0;
    z-index: 30;
    display: flex;
    justify-content: center;
    pointer-events: none;
  }

  .to-bottom button {
    display: grid;
    place-items: center;
    padding: 6px;
    border: 1px solid var(--color-gray-100);
    border-radius: var(--radius-pill);
    background-color: var(--color-white);
    pointer-events: auto;
  }

  :global([data-theme='dark']) .to-bottom button {
    border: 0;
    background-color: rgb(255 255 255 / 0.2);
  }

  .to-bottom button:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .inner {
    inline-size: 100%;
    max-inline-size: 928px;
  }
</style>
