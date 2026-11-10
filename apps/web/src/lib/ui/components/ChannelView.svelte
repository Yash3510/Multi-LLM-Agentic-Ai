<script lang="ts">
  // A channel (channels look §3): members and pinned messages in the header, the conversation
  // with reactions, replies, pins, edits and deletes (confirmed), who is typing, and the
  // composer. Presence and typing come from the fake source; webhooks are left out.
  import type { Channel, ChannelMessage, DataSource } from '$lib/data';
  import { renderMarkdown, safeHtml } from '$lib/ui/markdown';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import ConfirmDialog from './ConfirmDialog.svelte';

  type Props = { source: DataSource; channel: Channel; selfId: string };

  let { source, channel, selfId }: Props = $props();

  let messages = $state<ChannelMessage[]>([]);
  let draft = $state('');
  let replyTo = $state<ChannelMessage>();
  let editing = $state<{ id: string; text: string }>();
  let deleting = $state<ChannelMessage>();
  let pinnedOnly = $state(false);
  let typing = $state<string[]>([]);

  async function load() {
    messages = await source.listChannelMessages(channel.id);
  }

  $effect(() => {
    void channel.id;
    void load();
    const poll = setInterval(async () => (typing = await source.channelTyping(channel.id)), 3000);
    return () => clearInterval(poll);
  });

  const shown = $derived(pinnedOnly ? messages.filter((one) => one.pinned) : messages);
  const byId = $derived(new Map(messages.map((one) => [one.id, one])));
  const time = (at: Date) => at.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  // A message continues the one before when the same person wrote it within five minutes.
  const continues = (index: number) => {
    const [before, now] = [shown[index - 1], shown[index]];
    return Boolean(
      before &&
      before.userId === now.userId &&
      now.at.getTime() - before.at.getTime() < 300_000 &&
      !now.replyTo,
    );
  };

  async function send() {
    const content = draft.trim();
    if (!content) return;
    draft = '';
    await source.sendChannelMessage(channel.id, { content, replyTo: replyTo?.id });
    replyTo = undefined;
    await load();
  }

  function onkey(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void send();
    }
  }

  async function act(run: () => Promise<void>) {
    await run();
    await load();
  }

  async function saveEdit() {
    if (!editing) return;
    const { id, text } = editing;
    editing = undefined;
    await act(() => source.editChannelMessage(id, text));
  }

  async function remove() {
    if (!deleting) return;
    const id = deleting.id;
    deleting = undefined;
    await act(() => source.deleteChannelMessage(id));
  }
</script>

<div class="channel">
  <header class="bar">
    <span class="members" aria-hidden="true">
      {#each channel.members.slice(0, 3) as member, index (member)}
        <span class="avatar" style:z-index={3 - index}><Icon name="user" size={14} /></span>
      {/each}
      <span class="online"></span>
    </span>
    <h1 class="name">{channel.name}</h1>
    <button
      type="button"
      class="pill"
      aria-label="Pinned Messages"
      title="Pinned Messages"
      aria-pressed={pinnedOnly}
      onclick={() => (pinnedOnly = !pinnedOnly)}><Icon name="pin" size={16} /></button
    >
    <button type="button" class="pill" aria-label="Users" title="Users"
      ><Icon name="user" size={16} /><span class="count">{channel.members.length}</span></button
    >
  </header>

  <div class="messages">
    {#each shown as message, index (message.id)}
      {@const quoted = message.replyTo ? byId.get(message.replyTo) : undefined}
      <div class="message" data-message class:continued={continues(index)}>
        {#if message.pinned}<span class="tag">Pinned</span>{/if}
        {#if quoted}
          <p class="quote">
            <span class="mini"><Icon name="user" size={10} /></span><strong
              >{quoted.userName}</strong
            > <em>{quoted.content}</em>
          </p>
        {/if}
        <div class="line">
          {#if continues(index)}
            <span class="gutter"></span>
          {:else}
            <span class="photo"><Icon name="user" size={18} /></span>
          {/if}
          <div class="content">
            {#if !continues(index)}
              <p class="who">
                <strong>{message.userName}</strong> <span class="time">{time(message.at)}</span>
              </p>
            {/if}
            {#if editing?.id === message.id}
              <textarea class="edit" bind:value={editing.text} aria-label="Edit message" rows="2"
              ></textarea>
              <div class="edit-actions">
                <button type="button" onclick={() => (editing = undefined)}>Cancel</button>
                <button type="button" class="primary" onclick={saveEdit}>Save</button>
              </div>
            {:else}
              <div class="text" {@attach safeHtml(renderMarkdown(message.content))}></div>
              {#if message.edited}<span class="time">(edited)</span>{/if}
            {/if}
            {#if Object.keys(message.reactions).length}
              <div class="reactions">
                {#each Object.entries(message.reactions) as [emoji, who] (emoji)}
                  <button
                    type="button"
                    class="reaction"
                    class:mine={who.includes(selfId)}
                    onclick={() => act(() => source.reactChannelMessage(message.id, emoji))}
                    >{emoji} {who.length}</button
                  >
                {/each}
              </div>
            {/if}
          </div>
        </div>
        <div class="actions">
          <button
            type="button"
            aria-label="Add Reaction"
            title="Add Reaction"
            onclick={() => act(() => source.reactChannelMessage(message.id, '👍'))}
            ><Icon name="smiley" size={14} /></button
          >
          <button type="button" aria-label="Reply" title="Reply" onclick={() => (replyTo = message)}
            ><Icon name="arrow-left" size={14} /></button
          >
          <button
            type="button"
            aria-label={message.pinned ? 'Unpin' : 'Pin'}
            title={message.pinned ? 'Unpin' : 'Pin'}
            onclick={() => act(() => source.pinChannelMessage(message.id, !message.pinned))}
            ><Icon name="pin" size={14} /></button
          >
          {#if message.userId === selfId}
            <button
              type="button"
              aria-label="Edit"
              title="Edit"
              onclick={() => (editing = { id: message.id, text: message.content })}
              ><Icon name="rename" size={14} /></button
            >
            <button
              type="button"
              aria-label="Delete"
              title="Delete"
              onclick={() => (deleting = message)}><Icon name="trash" size={14} /></button
            >
          {/if}
        </div>
      </div>
    {:else}
      <p class="none">{pinnedOnly ? 'No pinned messages.' : 'No messages yet.'}</p>
    {/each}
  </div>

  <div class="composer-wrap">
    {#if typing.length}
      <p class="typing">
        {typing.join(', ')} is typing<span class="dots"><i></i><i></i><i></i></span>
      </p>
    {/if}
    {#if replyTo}
      <p class="replying">
        Replying to <strong>{replyTo.userName}</strong>
        <button type="button" aria-label="Cancel reply" onclick={() => (replyTo = undefined)}
          ><Icon name="x" size={14} /></button
        >
      </p>
    {/if}
    <div class="composer">
      <textarea
        bind:value={draft}
        onkeydown={onkey}
        placeholder="Message #{channel.name}"
        aria-label="Message"
        rows="1"></textarea>
      <button type="button" class="send" aria-label="Send" disabled={!draft.trim()} onclick={send}
        ><Icon name="send" size={16} /></button
      >
    </div>
  </div>
</div>

<ConfirmDialog
  open={deleting !== undefined}
  title="Delete Message"
  message="Are you sure you want to delete this message?"
  onconfirm={remove}
  oncancel={() => (deleting = undefined)}
/>

<style>
  .channel {
    display: flex;
    flex-direction: column;
    block-size: 100%;
    font-size: var(--text-ui);
  }
  .bar {
    position: sticky;
    top: 0;
    z-index: 30;
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 6px 10px;
    background: linear-gradient(var(--color-white) 60%, transparent);
  }
  :global([data-theme='dark']) .bar {
    background: linear-gradient(var(--color-gray-900) 60%, transparent);
  }
  .members {
    position: relative;
    display: flex;
    margin-inline-end: 6px;
  }
  .avatar {
    display: grid;
    place-items: center;
    inline-size: 26px;
    block-size: 26px;
    margin-inline-start: -6px;
    border: 2px solid var(--color-white);
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-200);
    color: var(--color-white);
  }
  .avatar:first-child {
    margin-inline-start: 0;
  }
  :global([data-theme='dark']) .avatar {
    border-color: var(--color-gray-900);
  }
  .online {
    position: absolute;
    inset-block-end: 0;
    inset-inline-start: 18px;
    inline-size: 8px;
    block-size: 8px;
    border-radius: var(--radius-pill);
    background-color: var(--color-green-500);
  }
  .name {
    flex: 1;
    overflow: hidden;
    font-size: var(--text-ui);
    font-weight: 400;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .pill {
    display: flex;
    align-items: center;
    gap: 2px;
    padding: 6px;
    border: 1px solid var(--color-gray-50);
    border-radius: 12px;
    color: var(--color-gray-600);
  }
  .pill:hover,
  .pill[aria-pressed='true'] {
    background-color: var(--color-gray-50);
  }
  :global([data-theme='dark']) .pill {
    border-color: var(--color-gray-850);
    color: var(--color-gray-400);
  }
  :global([data-theme='dark']) .pill:hover {
    background-color: var(--color-gray-850);
  }
  .messages {
    flex: 1;
    padding: 8px 12px;
    overflow-y: auto;
  }
  .message {
    position: relative;
    padding: 4px 8px;
    border-radius: 8px;
  }
  .message:hover {
    background-color: color-mix(in srgb, var(--color-gray-300) 5%, transparent);
  }
  .message.continued {
    padding-block-start: 0;
  }
  .tag {
    margin-inline-start: 40px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }
  .quote {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-inline-start: 48px;
    overflow: hidden;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    white-space: nowrap;
  }
  .quote em {
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .mini {
    display: grid;
    place-items: center;
    inline-size: 16px;
    block-size: 16px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-200);
    color: var(--color-white);
  }
  .line {
    display: flex;
    gap: 8px;
  }
  .photo,
  .gutter {
    flex-shrink: 0;
    inline-size: 32px;
  }
  .photo {
    display: grid;
    place-items: center;
    block-size: 32px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-200);
    color: var(--color-white);
  }
  .content {
    flex: 1;
    min-inline-size: 0;
  }
  .who strong {
    font-weight: var(--font-weight-medium);
  }
  .time {
    color: var(--color-gray-400);
    font-size: var(--text-caption);
  }
  .text {
    overflow-wrap: anywhere;
  }
  .reactions {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-block-start: 4px;
  }
  .reaction {
    padding: 2px 6px;
    border: 1px solid transparent;
    border-radius: 8px;
    background-color: var(--color-gray-100);
    font-size: var(--text-caption);
  }
  .reaction.mine {
    border-color: var(--color-blue-500);
  }
  :global([data-theme='dark']) .reaction {
    background-color: var(--color-gray-800);
  }
  .actions {
    position: absolute;
    inset-block-start: -14px;
    inset-inline-end: 4px;
    z-index: 5;
    display: none;
    gap: 4px;
    padding: 2px;
    border: 1px solid color-mix(in srgb, var(--color-gray-100) 30%, transparent);
    border-radius: 8px;
    background-color: var(--color-white);
    box-shadow:
      0 4px 6px -1px rgb(0 0 0 / 0.1),
      0 2px 4px -2px rgb(0 0 0 / 0.1);
  }
  :global([data-theme='dark']) .actions {
    background-color: var(--color-gray-850);
  }
  .message:hover .actions,
  .message:focus-within .actions {
    display: flex;
  }
  .actions button {
    display: grid;
    padding: 4px;
    border-radius: 8px;
  }
  .actions button:hover {
    background-color: var(--color-gray-100);
  }
  :global([data-theme='dark']) .actions button:hover {
    background-color: var(--color-gray-800);
  }
  .edit {
    inline-size: 100%;
    padding: 6px 8px;
    border: 1px solid var(--color-gray-200);
    border-radius: 8px;
    background: transparent;
    color: inherit;
    font-size: var(--text-ui);
  }
  .edit-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    font-size: var(--text-caption);
  }
  .edit-actions .primary {
    font-weight: var(--font-weight-medium);
  }
  .none {
    padding: 24px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    text-align: center;
  }
  .composer-wrap {
    padding: 0 12px 12px;
  }
  .typing,
  .replying {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 0 8px 4px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }
  .replying button {
    display: grid;
    margin-inline-start: auto;
  }
  .dots {
    display: inline-flex;
    gap: 2px;
    margin-inline-start: 4px;
  }
  .dots i {
    inline-size: 4px;
    block-size: 4px;
    border-radius: var(--radius-pill);
    background-color: currentcolor;
    animation: pulse 1.2s infinite;
  }
  .dots i:nth-child(2) {
    animation-delay: 0.2s;
  }
  .dots i:nth-child(3) {
    animation-delay: 0.4s;
  }
  @keyframes pulse {
    50% {
      opacity: 0.3;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .dots i {
      animation: none;
    }
  }
  .composer {
    display: flex;
    align-items: flex-end;
    gap: 8px;
    padding: 10px 12px;
    border: 1px solid var(--color-gray-100);
    border-radius: 24px;
  }
  :global([data-theme='dark']) .composer {
    border-color: var(--color-gray-850);
  }
  .composer textarea {
    flex: 1;
    max-block-size: 200px;
    background: transparent;
    color: inherit;
    font-size: var(--text-ui);
    resize: none;
    field-sizing: content;
  }
  .composer textarea:focus,
  .edit:focus {
    outline: none;
  }
  .send {
    display: grid;
    place-items: center;
    inline-size: 32px;
    block-size: 32px;
    border-radius: var(--radius-pill);
    background-color: var(--color-black);
    color: var(--color-white);
  }
  .send:disabled {
    opacity: 0.3;
  }
  :global([data-theme='dark']) .send {
    background-color: var(--color-white);
    color: var(--color-black);
  }
  :is(.pill, .actions button, .reaction, .send, .replying button):focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
