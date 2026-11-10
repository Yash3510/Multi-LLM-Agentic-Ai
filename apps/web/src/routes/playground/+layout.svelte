<script lang="ts">
  // The playground frame (playground look §3): Chat, Completions and Images.
  import { page } from '$app/state';
  import { resolve } from '$app/paths';

  let { children } = $props();

  const section = $derived(page.url.pathname.split('/')[2] ?? '');
</script>

<svelte:head><title>Playground / 4CE</title></svelte:head>

<div class="frame">
  <nav class="links" aria-label="Playground">
    <a href={resolve('/playground')} aria-current={section === '' ? 'page' : undefined}>Chat</a>
    <a
      href={resolve('/playground/completions')}
      aria-current={section === 'completions' ? 'page' : undefined}>Completions</a
    >
    <a href={resolve('/playground/images')} aria-current={section === 'images' ? 'page' : undefined}
      >Images</a
    >
  </nav>
  <div class="content">{@render children()}</div>
</div>

<style>
  .frame {
    display: flex;
    flex-direction: column;
    block-size: 100%;
  }
  .links {
    display: flex;
    gap: 4px;
    padding: 12px 10px 8px;
    font-size: var(--text-ui);
    line-height: 20px;
  }
  .links a {
    padding-inline: 4px;
    color: var(--color-gray-300);
    transition: color 150ms;
  }
  .links a:hover {
    color: var(--color-gray-700);
  }
  .links a[aria-current] {
    color: inherit;
  }
  :global([data-theme='dark']) .links a {
    color: var(--color-gray-600);
  }
  :global([data-theme='dark']) .links a[aria-current] {
    color: inherit;
  }
  .content {
    flex: 1;
    min-block-size: 0;
  }
</style>
