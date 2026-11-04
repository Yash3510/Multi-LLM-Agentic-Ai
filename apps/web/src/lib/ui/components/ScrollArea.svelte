<script lang="ts">
  // A scrolling region with a stable gutter, so nothing shifts when the scrollbar appears. It joins
  // the tab order only while it actually scrolls, so a keyboard can reach and scroll it, and it then
  // carries its name as a region. Focus outlines inside turn inward, where they cannot be clipped.
  // A line-1 hairline marks each edge with more content beyond it; the hairline space is always
  // held, so showing it moves nothing.
  import type { Snippet } from 'svelte';
  import type { HTMLAttributes } from 'svelte/elements';

  type Props = HTMLAttributes<HTMLDivElement> & {
    /** The region's name, used while it scrolls. */
    label?: string;
    orientation?: 'vertical' | 'horizontal';
    /** The size past which it scrolls, e.g. "20rem". */
    maxBlockSize?: string;
    children: Snippet;
  };

  let {
    label,
    orientation = 'vertical',
    maxBlockSize,
    children,
    class: className,
    ...rest
  }: Props = $props();

  let node = $state<HTMLDivElement>();
  let inner = $state<HTMLDivElement>();
  let scrollable = $state(false);
  let moreBefore = $state(false);
  let moreAfter = $state(false);

  function measure() {
    if (!node) return;
    const vertical = orientation === 'vertical';
    const position = vertical ? node.scrollTop : Math.abs(node.scrollLeft);
    const visible = vertical ? node.clientHeight : node.clientWidth;
    const total = vertical ? node.scrollHeight : node.scrollWidth;
    // One pixel of slack: zoomed layouts report fractional sizes.
    scrollable = total - visible > 1;
    moreBefore = scrollable && position > 1;
    moreAfter = scrollable && position + visible < total - 1;
  }

  // Set from script: a region that scrolls has to be reachable by keyboard (WCAG 2.1.1), and one
  // that does not scroll must not add a stop to the tab order.
  $effect(() => {
    if (!node) return;
    if (scrollable) {
      node.tabIndex = 0;
      if (label) {
        node.setAttribute('role', 'region');
        node.setAttribute('aria-label', label);
      }
    } else {
      node.removeAttribute('tabindex');
      node.removeAttribute('role');
      node.removeAttribute('aria-label');
    }
  });

  $effect(() => {
    if (!node || !inner) return;
    measure();
    // jsdom, which component tests run in, has no ResizeObserver.
    if (!globalThis.ResizeObserver) return;
    const observer = new ResizeObserver(measure);
    observer.observe(node);
    observer.observe(inner);
    return () => observer.disconnect();
  });
</script>

<div
  bind:this={node}
  {...rest}
  class={['scroll-area focus-inset', className]}
  data-orientation={orientation}
  data-more-before={moreBefore || undefined}
  data-more-after={moreAfter || undefined}
  style:max-block-size={maxBlockSize}
  onscroll={measure}
>
  <div bind:this={inner} class="inner">
    {@render children()}
  </div>
</div>

<style>
  .scroll-area {
    min-block-size: 0;
    scrollbar-gutter: stable;
    scrollbar-width: thin;
    scrollbar-color: var(--color-line-control) transparent;
    overscroll-behavior: contain;
    border: 0 solid transparent;
    transition: border-color var(--duration-quick) var(--ease-out);
  }

  .scroll-area[data-orientation='vertical'] {
    overflow-x: hidden;
    overflow-y: auto;
    border-block-width: 1px;
  }

  .scroll-area[data-orientation='horizontal'] {
    overflow-x: auto;
    overflow-y: hidden;
    border-inline-width: 1px;
  }

  .scroll-area[data-orientation='horizontal'] .inner {
    inline-size: max-content;
    min-inline-size: 100%;
  }

  .scroll-area[data-orientation='vertical'][data-more-before] {
    border-block-start-color: var(--color-line-1);
  }

  .scroll-area[data-orientation='vertical'][data-more-after] {
    border-block-end-color: var(--color-line-1);
  }

  .scroll-area[data-orientation='horizontal'][data-more-before] {
    border-inline-start-color: var(--color-line-1);
  }

  .scroll-area[data-orientation='horizontal'][data-more-after] {
    border-inline-end-color: var(--color-line-1);
  }
</style>
