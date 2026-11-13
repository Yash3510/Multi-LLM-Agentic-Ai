<script lang="ts">
  // The sign-off panel (own-4ce look S13, features F29-F35), docked where the message box sits:
  // the draft beside what was checked and which sources it rests on, then the person types
  // "approve" to release it or withholds it. Anything other than approve keeps it back.
  import type { SignOffRequest, Source } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { markChanges, onChip, renderMarkdown, safeHtml } from '$lib/ui/markdown';

  type Props = {
    request: SignOffRequest;
    draft: string;
    sources: Source[];
    model: string;
    ondecide: (outcome: 'released' | 'withheld') => void;
  };

  let { request, draft, sources, model, ondecide }: Props = $props();

  let word = $state('');
  let refused = $state(false);
  let showChanges = $state(false);
  const revision = $derived(request.revision);
  // Removals with no replacement are listed in the box; the rest are marked in the draft.
  const takenOut = $derived(
    (revision?.changes ?? []).filter((change) => change.removed && !change.added),
  );
  const ready = $derived(word.trim().toLowerCase() === 'approve');
  const passed = $derived(request.checks.every((check) => check.verdict === 'pass'));
  const cited = $derived(
    new Set([...draft.matchAll(/\[(\d+)\]/g)].map((match) => Number(match[1]))),
  );
  const html = $derived(renderMarkdown(draft, sources));

  // The draft's links (look S13): a hovered check lights the blocks citing its sources; a chip in
  // the draft opens its passage in a card under its block (press again to close).
  let draftNode: HTMLElement | undefined;
  const BLOCKS = 'p, li, td, h1, h2, h3, h4';

  function highlight(cites: number[] = []) {
    if (!draftNode) return;
    draftNode.querySelectorAll('[data-hl]').forEach((block) => block.removeAttribute('data-hl'));
    for (const index of cites)
      draftNode
        .querySelectorAll(`.chip[data-source="${index}"]`)
        .forEach((chip) => chip.closest(BLOCKS)?.setAttribute('data-hl', ''));
  }

  function openPassage(index: number) {
    const source = sources.find((item) => item.index === index);
    const chip = draftNode?.querySelector(`.chip[data-source="${index}"]`);
    const block = chip?.closest(BLOCKS);
    const open = draftNode?.querySelector('.passage-card');
    const same = open?.getAttribute('data-source') === String(index);
    open?.remove();
    draftNode
      ?.querySelectorAll('.chip[data-open]')
      .forEach((item) => item.removeAttribute('data-open'));
    if (same || !source || !block) return;
    const card = document.createElement('div');
    card.className = 'passage-card';
    card.setAttribute('data-source', String(index));
    const head = document.createElement('div');
    head.className = 'passage-head';
    const label = document.createElement('span');
    label.textContent = 'Passage';
    const name = document.createElement('b');
    name.textContent = source.title;
    head.append(label, name);
    const body = document.createElement('p');
    body.textContent = source.passage || 'No passage.';
    card.append(head, body);
    block.after(card);
    chip?.setAttribute('data-open', '');
  }

  function approve() {
    if (!ready) {
      refused = true;
      return;
    }
    ondecide('released');
  }
</script>

<section class="card" aria-label="Review before release">
  <header class="head">
    <div class="title-row">
      <h2 class="title">Review before release</h2>
      <span class="verdict" data-passed={passed ? '' : undefined}>
        {passed ? 'Passed by Challenger' : 'Did not pass its checks'}
      </span>
    </div>
    <span class="drafted">Drafted on <code>{model}</code></span>
  </header>

  <div class="body">
    <div class="draft">
      {#if revision}
        <button
          type="button"
          class="changes-toggle"
          aria-pressed={showChanges}
          onclick={() => (showChanges = !showChanges)}
        >
          {showChanges ? 'Hide the changes' : 'Show what changed since try 1'}
        </button>
        {#if showChanges}
          <div class="changes">
            {#each revision.objections as objection (objection.text)}
              <p>{objection.by.toUpperCase()} on try {revision.try - 1}: “{objection.text}”</p>
            {/each}
            {#each takenOut as change, index (index)}
              <p class="taken">Taken out: <s>{change.removed}</s></p>
            {/each}
          </div>
        {/if}
      {/if}
      {#if draft.trim()}
        <div
          class="draft-text"
          {@attach safeHtml(html)}
          {@attach markChanges(revision?.changes ?? [], showChanges)}
          {@attach (node) => {
            draftNode = node;
          }}
          {@attach onChip(openPassage)}
        ></div>
      {:else}
        <p class="empty">The draft is empty.</p>
      {/if}
    </div>
    <div class="side">
      <h3 class="section">Checked</h3>
      <ul class="checks">
        {#each request.checks as check (check.label)}
          <li
            class="check"
            onmouseenter={() => highlight(check.cites)}
            onmouseleave={() => highlight()}
          >
            <span class="mark" data-verdict={check.verdict} aria-hidden="true">
              <Icon
                name={check.verdict === 'pass'
                  ? 'verdict-pass'
                  : check.verdict === 'fail'
                    ? 'verdict-fail'
                    : 'verdict-review'}
                size={14}
              />
            </span>
            <span>
              {check.label}
              <span class="by">Challenger</span>
            </span>
          </li>
        {/each}
      </ul>
      {#if sources.length}
        <h3 class="section">Sources</h3>
        <ul class="sources">
          {#each sources as source (source.index)}
            <li class="source" data-cited={cited.has(source.index) ? '' : undefined}>
              <span class="source-name">{source.title}</span>
              <span class="tag">{cited.has(source.index) ? 'cited' : 'not cited'}</span>
            </li>
          {/each}
        </ul>
      {/if}
    </div>
  </div>

  <div class="controls">
    <span class="field-box">
      <input
        class="field"
        bind:value={word}
        placeholder="Type approve to release"
        aria-label="Type approve to release"
        oninput={() => (refused = false)}
        onkeydown={(event) => {
          if (event.key === 'Enter') approve();
          if (event.key === 'Escape') word = '';
        }}
      />
      {#if ready}<span class="tick" aria-hidden="true"><Icon name="check" size={16} /></span>{/if}
    </span>
    <button type="button" class="withhold" onclick={() => ondecide('withheld')}>Withhold</button>
    <button type="button" class="approve" data-ready={ready ? '' : undefined} onclick={approve}>
      Approve
    </button>
  </div>
  <p class="hint" data-refused={refused ? '' : undefined}>
    {refused
      ? 'Type approve to release it.'
      : 'Nothing enters the conversation until you approve it. Withhold, press Esc, or leave it - anything other than approve keeps it back.'}
  </p>
</section>

<style>
  .card {
    overflow: hidden;
    border: 1px solid var(--color-gray-100);
    border-radius: 20px;
    background-color: var(--color-white);
    box-shadow:
      0 0 0 1px rgb(0 0 0 / 0.04),
      0 1px 3px -1px rgb(16 24 40 / 0.08),
      0 20px 48px -18px rgb(16 24 40 / 0.28);
    animation: dock 280ms ease-out;
  }

  :global([data-theme='dark']) .card {
    border-color: var(--color-gray-850);
    background-color: var(--color-gray-900);
    box-shadow:
      0 0 0 1px rgb(255 255 255 / 0.06),
      0 1px 3px -1px rgb(16 24 40 / 0.08),
      0 20px 48px -18px rgb(16 24 40 / 0.28);
  }

  .head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 6px var(--spacing-4);
    padding: var(--spacing-4) 29px var(--spacing-3);
  }

  .title-row {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .title {
    color: var(--color-gray-900);
    font-size: var(--text-body);
    font-weight: var(--font-weight-medium);
  }

  :global([data-theme='dark']) .title {
    color: var(--color-gray-100);
  }

  .verdict {
    padding: 2px 10px;
    border-radius: var(--radius-pill);
    background-color: var(--color-amber-50);
    color: var(--color-amber-700);
    font-size: var(--text-micro);
    font-weight: var(--font-weight-medium);
  }

  .verdict[data-passed] {
    background-color: var(--color-emerald-50);
    color: var(--color-emerald-700);
  }

  .drafted {
    color: var(--color-gray-600);
    font-size: var(--text-caption);
  }

  .drafted code {
    padding: 2px 4px;
    border-radius: 4px;
    background-color: var(--color-gray-100);
    font-family: var(--font-mono);
    font-size: var(--text-micro);
  }

  .body {
    display: grid;
    margin: 0 var(--spacing-3) var(--spacing-3);
    overflow: hidden;
    border: 1px solid var(--color-gray-100);
    border-radius: 16px;
  }

  @media (min-width: 48rem) {
    .body {
      grid-template-columns: minmax(0, 1fr) 15rem;
    }

    .side {
      border-inline-start: 1px solid var(--color-gray-100);
    }
  }

  .draft {
    max-block-size: 42vh;
    padding: var(--spacing-4);
    overflow-y: auto;
    background-color: var(--color-gray-50);
    color: var(--color-gray-900);
    font-size: var(--text-body);
    line-height: 1.625;
  }

  .draft-text :global(p + p) {
    margin-block-start: var(--spacing-3);
  }

  /* Tables and lists in the draft read as in the answer. */
  .draft-text :global(table) {
    margin-block: var(--spacing-2);
    border-collapse: collapse;
    font-size: var(--text-small);
  }

  .draft-text :global(:is(th, td)) {
    padding: var(--spacing-1) var(--spacing-3);
    border-block-end: 1px solid var(--color-line-1);
  }

  .draft-text :global(:is(th, td):not([align])) {
    text-align: start;
  }

  .draft-text :global(th) {
    font-weight: var(--font-weight-medium);
  }

  .draft-text :global(ul) {
    padding-inline-start: 1.5em;
    list-style: disc;
  }

  .draft-text :global(.chip) {
    padding: 1px 6px;
    border: 1px solid var(--color-gray-200);
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-50);
    font-size: 0.66rem;
    font-style: normal;
    font-weight: var(--font-weight-medium);
  }

  /* What changed since try 1 (look S13). */
  .changes-toggle {
    display: inline-flex;
    margin-block-end: var(--spacing-3);
    padding: 4px var(--spacing-3);
    border: 1px solid var(--color-gray-200);
    border-radius: var(--radius-pill);
    color: var(--color-gray-600);
    font-size: var(--text-caption);
    transition:
      border-color 150ms,
      color 150ms;
  }

  .changes-toggle:hover,
  .changes-toggle[aria-pressed='true'] {
    border-color: var(--color-gray-900);
    color: var(--color-gray-900);
  }

  .changes-toggle:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .changes {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);
    margin-block-end: var(--spacing-3);
    padding: var(--spacing-2) var(--spacing-3);
    border-radius: var(--radius-inset);
    background-color: var(--color-amber-50);
    color: var(--color-amber-800);
    font-size: 12.5px;
    line-height: 1.625;
    animation: enter-changes 260ms;
  }

  .taken {
    color: var(--color-gray-600);
  }

  /* A hovered check's blocks (look S13). */
  .draft-text :global([data-hl]) {
    border-radius: 6px;
    background-color: rgb(139 92 246 / 0.09);
    box-shadow: 0 0 0 3px rgb(139 92 246 / 0.09);
    transition:
      background-color 300ms,
      box-shadow 300ms;
  }

  .draft-text :global(.chip[data-open]) {
    border-color: var(--color-gray-500);
    color: var(--color-gray-900);
  }

  /* The passage card under a pressed chip's block. */
  .draft-text :global(.passage-card) {
    margin-block: 5.6px var(--spacing-3);
    padding: 9.6px var(--spacing-3);
    border: 1px solid var(--color-gray-100);
    border-radius: var(--radius-inset);
    background-color: var(--color-white);
    box-shadow: 0 14px 30px -20px rgb(16 24 40 / 0.35);
    animation: enter-changes 320ms cubic-bezier(0.22, 1, 0.36, 1);
  }

  .draft-text :global(.passage-head) {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    margin-block-end: var(--spacing-1);
    color: var(--color-gray-500);
    font-size: var(--text-micro);
  }

  .draft-text :global(.passage-head b) {
    color: var(--color-gray-700);
    font-weight: var(--font-weight-medium);
  }

  .draft-text :global(.passage-card p) {
    margin: 0;
    color: var(--color-gray-600);
    font-size: 12.5px;
    line-height: 1.6;
  }

  .draft-text :global([data-changed]) {
    border-radius: 6px;
    background-color: rgb(16 185 129 / 0.08);
    box-shadow: 0 0 0 3px rgb(16 185 129 / 0.08);
  }

  .draft-text :global([data-was]) {
    padding-inline: var(--spacing-1);
    border-radius: 5px;
    background-color: rgb(239 68 68 / 0.08);
    color: var(--color-red-700);
    text-decoration: line-through;
    text-decoration-color: rgb(185 28 28 / 0.4);
  }

  @keyframes enter-changes {
    from {
      opacity: 0;
      translate: 0 -4px;
    }
  }

  .empty {
    font-style: italic;
  }

  .side {
    max-block-size: 42vh;
    padding: 14px var(--spacing-3);
    overflow-y: auto;
    font-size: 12.5px;
  }

  .section {
    margin-block-end: 6px;
    color: var(--color-gray-500);
    font-size: var(--text-tag);
    font-weight: var(--font-weight-medium);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .checks {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin-block-end: var(--spacing-3);
  }

  .check {
    display: grid;
    grid-template-columns: 14.4px 1fr;
    gap: 6px;
    margin-inline: -6px;
    padding: 6px 4px;
    border-radius: 8px;
    color: var(--color-gray-700);
    line-height: 1.45;
    transition: background-color 150ms;
  }

  .check:hover {
    background-color: var(--color-gray-50);
  }

  .mark {
    display: inline-flex;
    padding-block-start: 2px;
    color: var(--color-amber-600);
  }

  .mark[data-verdict='pass'] {
    color: var(--color-emerald-600);
  }

  .by {
    display: block;
    color: var(--color-gray-500);
    font-size: var(--text-tag);
    letter-spacing: 0.04em;
  }

  .source {
    display: flex;
    align-items: baseline;
    gap: var(--spacing-2);
    padding: 6px 4px;
    border-radius: 8px;
    color: var(--color-gray-600);
  }

  .source[data-cited] {
    color: var(--color-gray-900);
    font-weight: var(--font-weight-medium);
  }

  .source-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .tag {
    color: var(--color-gray-500);
    font-size: var(--text-tag);
    font-weight: var(--font-weight-normal);
  }

  .controls {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-2);
    padding: 0 var(--spacing-3) var(--spacing-2);
  }

  .field-box {
    position: relative;
    flex: 1 1 100%;
  }

  @media (min-width: 40rem) {
    .field-box {
      flex-basis: 0;
    }
  }

  .field {
    inline-size: 100%;
    padding: 10px 40px 10px var(--spacing-4);
    border: 1px solid var(--color-gray-200);
    border-radius: var(--radius-inset);
    background-color: color-mix(in srgb, var(--color-gray-50) 70%, transparent);
    color: var(--color-gray-900);
    font-size: var(--text-ui);
    line-height: 20px;
    transition:
      border-color 200ms,
      background-color 200ms,
      box-shadow 200ms;
  }

  .field::placeholder {
    color: var(--color-gray-500);
  }

  .field:focus {
    outline: none;
    border-color: var(--color-gray-900);
    background-color: var(--color-white);
    box-shadow: 0 0 0 4px rgb(22 22 22 / 0.06);
  }

  .tick {
    position: absolute;
    inset-block: 0;
    inset-inline-end: 14px;
    display: grid;
    place-items: center;
    color: var(--color-emerald-600);
    animation: pop 300ms ease-out;
  }

  .withhold,
  .approve {
    padding: 10px var(--spacing-4);
    border-radius: var(--radius-pill);
    font-size: var(--text-ui);
    font-weight: var(--font-weight-medium);
    line-height: 20px;
    transition:
      background-color 300ms,
      color 300ms;
  }

  .withhold {
    border: 1px solid var(--color-gray-200);
    color: var(--color-gray-700);
  }

  .withhold:hover {
    background-color: var(--color-gray-50);
  }

  .approve {
    min-inline-size: 120px;
    padding-inline: 20px;
    background-color: var(--color-gray-100);
    color: var(--color-gray-500);
  }

  .approve[data-ready] {
    background-color: var(--color-gray-900);
    color: var(--color-white);
  }

  .approve[data-ready]:hover {
    background-color: var(--color-gray-800);
  }

  :is(.withhold, .approve):focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .hint {
    padding: 0 29px 14px;
    color: var(--color-gray-600);
    font-size: 11.5px;
  }

  .hint[data-refused] {
    color: var(--color-amber-700);
  }

  @keyframes dock {
    from {
      opacity: 0;
      translate: 0 16px;
    }
  }

  @keyframes pop {
    from {
      opacity: 0;
      scale: 0.75;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .card,
    .tick {
      animation: none;
    }
  }
</style>
