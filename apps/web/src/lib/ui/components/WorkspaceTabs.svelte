<script lang="ts">
  // The workspace's tab row (workspace look §1.2): five links with their counts at 60 %. The
  // current tab is ink; the others are faint and darken on hover. No pill, no underline.
  import type { WorkspaceTab } from '$lib/data';
  import { resolve } from '$app/paths';

  type Props = { current: WorkspaceTab; counts: Record<WorkspaceTab, number> };

  let { current, counts }: Props = $props();

  const TABS: { tab: WorkspaceTab; label: string }[] = [
    { tab: 'models', label: 'Models' },
    { tab: 'knowledge', label: 'Knowledge' },
    { tab: 'prompts', label: 'Prompts' },
    { tab: 'skills', label: 'Skills' },
    { tab: 'tools', label: 'Tools' },
  ];
  const short = new Intl.NumberFormat('en', { notation: 'compact' });
</script>

<nav class="tabs" aria-label="Workspace">
  {#each TABS as { tab, label } (tab)}
    <a
      class="tab"
      href={resolve(`/workspace/${tab}`)}
      aria-current={tab === current ? 'page' : undefined}
      draggable="false"
    >
      {label}
      <span class="count">{short.format(counts[tab] ?? 0)}</span>
    </a>
  {/each}
</nav>

<style>
  .tabs {
    display: flex;
    align-items: center;
    gap: 2px;
    min-inline-size: 0;
    margin-inline-end: 6px;
    padding-block: 4px;
    overflow-x: auto;
    scrollbar-width: none;
    font-size: var(--text-ui);
    line-height: 20px;
  }

  @media (min-width: 48rem) {
    .tabs {
      gap: 4px;
    }
  }

  .tab {
    display: inline-flex;
    flex-shrink: 0;
    align-items: center;
    gap: 4px;
    padding-inline: 4px;
    color: var(--color-gray-300);
    text-decoration: none;
    user-select: none;
    transition: color 150ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  .tab:hover {
    color: var(--color-gray-700);
  }

  .tab[aria-current] {
    color: var(--color-gray-900);
  }

  :global([data-theme='dark']) .tab {
    color: var(--color-gray-600);
  }

  :global([data-theme='dark']) .tab:hover {
    color: var(--color-white);
  }

  :global([data-theme='dark']) .tab[aria-current] {
    color: var(--color-gray-100);
  }

  .count {
    opacity: 0.6;
  }

  .tab:focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }
</style>
