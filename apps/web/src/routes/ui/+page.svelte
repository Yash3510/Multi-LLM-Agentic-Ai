<script lang="ts">
  // The design reference. Every file in ./sections is a section, in file-name order; each exports
  // `section` (its anchor and title) from its module script. Add a section by adding a file.
  import type { Component } from 'svelte';
  import { m } from '$lib/i18n/generated/messages.js';
  import type { SectionMeta } from './section';

  type SectionModule = { default: Component; section: SectionMeta };

  const sections = Object.entries(
    import.meta.glob<SectionModule>('./sections/*.svelte', { eager: true }),
  )
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([path, module]) => ({
      // The file's number prefix ("00-colours.svelte") is the section's number on the page.
      number: path.match(/\/(\d+)-/)?.[1] ?? '',
      meta: module.section,
      Content: module.default,
    }));

  // The section nearest the top of the viewport is "current" in the index.
  let current = $state(sections[0]?.meta.id);

  $effect(() => {
    // Plain bookkeeping for the observer, not state: only `current` drives the page.
    const visible: Record<string, boolean> = {};
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) visible[entry.target.id] = entry.isIntersecting;
        current = sections.find(({ meta }) => visible[meta.id])?.meta.id ?? current;
      },
      // A band across the upper part of the viewport, below the sticky toolbar.
      { rootMargin: '-15% 0px -55% 0px' },
    );
    for (const { meta } of sections) {
      const element = document.getElementById(meta.id);
      if (element) observer.observe(element);
    }
    return () => observer.disconnect();
  });
</script>

<div class="reference mx-auto max-w-7xl px-6 pt-10 pb-12">
  <nav class="index hidden lg:block" aria-label={m.ui_nav()}>
    <p class="mb-2 px-3 text-caption text-ink-3">{m.ui_nav()}</p>
    <ol class="flex flex-col gap-0.5">
      {#each sections as { number, meta } (meta.id)}
        <li>
          <a
            class="index-link flex h-8 items-center gap-3 rounded-control px-3 text-small text-ink-2"
            href="#{meta.id}"
            aria-current={current === meta.id ? 'location' : undefined}
          >
            <span class="font-mono text-caption text-ink-3 tabular">{number}</span>
            {meta.title()}
          </a>
        </li>
      {/each}
    </ol>
  </nav>

  <main class="min-w-0">
    <header class="flex flex-col gap-2 pb-10">
      <h1 class="text-heading text-ink-1">{m.ui_title()}</h1>
      <p class="max-w-prose text-body text-ink-2">{m.ui_intro()}</p>
    </header>

    <div class="flex flex-col">
      {#each sections as { number, meta, Content } (meta.id)}
        <section
          id={meta.id}
          aria-labelledby="{meta.id}-title"
          class="flex flex-col gap-6 border-t border-line-1 pt-8 pb-12"
        >
          <header class="flex flex-col gap-1">
            <h2 id="{meta.id}-title" class="flex items-baseline gap-3 text-title text-ink-1">
              <span class="font-mono text-small font-normal text-ink-3 tabular">{number}</span>
              {meta.title()}
            </h2>
            {#if meta.description}
              <p class="max-w-prose text-ui text-ink-2">{meta.description()}</p>
            {/if}
          </header>
          <Content />
        </section>
      {/each}
    </div>
  </main>
</div>

<style>
  .reference {
    display: grid;
    gap: var(--spacing-10);
  }

  @media (min-width: 64rem) {
    .reference {
      grid-template-columns: calc(var(--spacing-12) * 4) minmax(0, 1fr);
    }
  }

  .index {
    position: sticky;
    /* Below the sticky toolbar, aligned with the page title. */
    top: calc(var(--spacing-12) * 2);
    align-self: start;
  }

  section {
    scroll-margin-top: calc(var(--spacing-12) + var(--spacing-8));
  }

  .index-link {
    position: relative;
    transition-property: background-color, color;
    transition-duration: var(--duration-quick);
    transition-timing-function: var(--ease-out);
  }

  .index-link:hover {
    background-color: var(--color-tint);
    color: var(--color-ink-1);
  }

  /* Current: the tint fill and full ink, as the sidebar's current row. No edge bar. */
  .index-link[aria-current] {
    background-color: var(--color-tint);
    color: var(--color-ink-1);
    font-weight: var(--font-weight-medium);
  }
</style>
