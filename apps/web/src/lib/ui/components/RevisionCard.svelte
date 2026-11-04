<script lang="ts">
  // What changed on a later try (own-4ce look S8, features F38): the objection from the previous
  // try, the Author's fixes, and how the Challenger judged the revised draft.
  import type { Revision } from '$lib/data';

  let { revision, passed }: { revision: Revision; passed: boolean } = $props();

  let open = $state(false);
  const title = $derived(`What changed on try ${revision.try}`);
  const fixes = $derived(revision.changes.slice(0, 1));
  const others = $derived(revision.changes.slice(1));
</script>

<div class="card" role="group" aria-label={title}>
  <div class="head">
    <span class="heading">{title}</span>
    <span class="verdict" data-passed={passed ? '' : undefined}>
      {passed ? `Passed on try ${revision.try}` : `Still failed on try ${revision.try}`}
    </span>
  </div>
  {#each revision.objections as objection (objection.text)}
    <div class="row">
      <span class="label">{objection.by.toUpperCase()} · try {revision.try - 1}</span>
      <span class="text"><span class="cross">✕</span>{objection.text}</span>
    </div>
  {/each}
  <div class="row">
    <span class="label">AUTHOR · try {revision.try}</span>
    <span class="stack">
      {#each fixes as change, index (index)}
        {#if change.removed}<span class="removed">{change.removed}</span>{/if}
        {#if change.added}<span class="added">{change.added}</span>{/if}
      {/each}
    </span>
  </div>
  <div class="row">
    <span class="label">CHALLENGER · try {revision.try}</span>
    <span class="text">
      {#if passed}<span class="tick">✓</span>Passed the revised draft.{:else}<span class="cross"
          >✕</span
        >Failed the revised draft too; the reviewer saw that before deciding.{/if}
    </span>
  </div>
  {#if others.length}
    <div class="foot">
      <span>Also changed: {others.length} {others.length === 1 ? 'edit' : 'edits'}</span>
      <button type="button" class="toggle" onclick={() => (open = !open)}>
        {open ? 'Hide the changes' : 'Show every change'}
      </button>
    </div>
    {#if open}
      <ul class="list">
        {#each others as change, index (index)}
          <li class="item">
            {#if change.removed}<span class="removed">{change.removed}</span>{/if}
            {#if change.added}<span class="added">{change.added}</span>{/if}
          </li>
        {/each}
      </ul>
    {/if}
  {/if}
</div>

<style>
  .card {
    margin-block-start: 10px;
    padding: var(--spacing-2) var(--spacing-3);
    border: 1px solid color-mix(in srgb, var(--color-gray-200) 80%, transparent);
    border-radius: 16px;
  }

  :global([data-theme='dark']) .card {
    border-color: var(--color-gray-800);
  }

  .head {
    display: flex;
    justify-content: space-between;
    gap: var(--spacing-3);
    margin-block-end: var(--spacing-1);
  }

  .heading,
  .label {
    color: var(--color-gray-600);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .heading {
    font-size: var(--text-tag);
    font-weight: var(--font-weight-medium);
  }

  .verdict {
    color: var(--color-amber-700);
    font-size: var(--text-micro);
    font-weight: var(--font-weight-medium);
  }

  .verdict[data-passed] {
    color: var(--color-emerald-700);
  }

  .row {
    display: grid;
    grid-template-columns: 6.5rem minmax(0, 1fr);
    gap: 10px;
    padding-block: 4.8px;
    font-size: 12.5px;
    line-height: 1.5;
  }

  @media (max-width: 30rem) {
    .row {
      grid-template-columns: 1fr;
      gap: 2px;
    }
  }

  .label {
    padding-block-start: 2px;
    font-size: 10px;
  }

  .text {
    color: var(--color-gray-700);
  }

  :global([data-theme='dark']) .text {
    color: var(--color-gray-300);
  }

  .cross,
  .tick {
    margin-inline-end: var(--spacing-1);
    font-weight: var(--font-weight-semibold);
  }

  .cross {
    color: var(--color-amber-700);
  }

  .tick {
    color: var(--color-emerald-700);
  }

  .stack,
  .item {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-1);
  }

  .removed,
  .added {
    padding-inline: 5px;
    border-radius: 5px;
  }

  .removed {
    background-color: var(--color-red-50);
    color: var(--color-red-700);
    text-decoration: line-through;
    text-decoration-color: color-mix(in srgb, var(--color-red-700) 45%, transparent);
  }

  .added {
    background-color: var(--color-emerald-50);
    color: var(--color-emerald-700);
  }

  .foot {
    display: flex;
    justify-content: space-between;
    gap: var(--spacing-3);
    margin-block-start: var(--spacing-1);
    padding-block-start: 6px;
    border-block-start: 1px solid var(--color-gray-100);
    color: var(--color-gray-600);
    font-size: var(--text-caption);
  }

  .toggle {
    padding: 2px var(--spacing-2);
    border-radius: var(--radius-pill);
    color: var(--color-gray-900);
    font-weight: var(--font-weight-medium);
  }

  .toggle:hover {
    background-color: var(--color-gray-100);
  }

  .toggle:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
    margin-block-start: var(--spacing-2);
    padding-block-end: var(--spacing-1);
    animation: fade 220ms ease-out;
  }

  .item {
    padding-inline-start: 10px;
    border-inline-start: 2px solid var(--color-gray-100);
    font-size: 12.5px;
    line-height: 1.375;
  }

  @keyframes fade {
    from {
      opacity: 0;
    }
  }
</style>
