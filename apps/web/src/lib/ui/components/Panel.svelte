<script lang="ts">
  // The docked panel that dialogs, sheets and the side panel share: e3 on the panel radius. A header
  // with the title, an optional description and trailing controls (the close button); a body that
  // scrolls on its own, with hairlines where more content waits; and the actions in one
  // leading-aligned row under the content, primary first, each named by verb and object.
  //
  // Other attributes land on the panel itself, so a dialog's behaviour layer can make the panel its
  // own element. Pass titleId and descriptionId to name it from outside.
  import type { Snippet } from 'svelte';
  import type { HTMLAttributes } from 'svelte/elements';
  import ScrollArea from './ScrollArea.svelte';
  import './surfaces.css';

  type Props = Omit<HTMLAttributes<HTMLElement>, 'title'> & {
    title: string;
    description?: string;
    titleId?: string;
    descriptionId?: string;
    /** The heading level of the title. */
    level?: 2 | 3;
    element?: 'section' | 'div' | 'aside';
    /** Trailing header controls, such as the close button. */
    headerEnd?: Snippet;
    /** A row under the title: tabs or a search field. */
    toolbar?: Snippet;
    children: Snippet;
    actions?: Snippet;
    /** The title element, so a container can move focus to it. */
    heading?: HTMLElement;
    /** The panel element itself. */
    ref?: HTMLElement;
  };

  let {
    title,
    description,
    titleId,
    descriptionId,
    level = 2,
    element = 'section',
    headerEnd,
    toolbar,
    children,
    actions,
    heading = $bindable(),
    ref = $bindable(),
    class: className,
    ...rest
  }: Props = $props();

  const id = $props.id();
  const ownTitleId = $derived(titleId ?? `${id}-title`);
  const ownDescriptionId = $derived(descriptionId ?? `${id}-description`);
</script>

<svelte:element
  this={element}
  bind:this={ref}
  aria-labelledby={ownTitleId}
  aria-describedby={description ? ownDescriptionId : undefined}
  {...rest}
  class={['panel', className]}
  data-surface="panel"
>
  <div class="head">
    <div class="flex min-w-0 flex-1 flex-col gap-1">
      <svelte:element
        this={`h${level}`}
        bind:this={heading}
        id={ownTitleId}
        class="title text-title text-ink-1"
        tabindex="-1"
      >
        {title}
      </svelte:element>
      {#if description}
        <p id={ownDescriptionId} class="text-small text-ink-2">{description}</p>
      {/if}
    </div>
    {#if headerEnd}
      <div class="-my-1 flex shrink-0 items-center gap-1">{@render headerEnd()}</div>
    {/if}
  </div>

  {#if toolbar}
    <div class="toolbar">{@render toolbar()}</div>
  {/if}

  <ScrollArea class="body" label={title}>
    <div class="body-inner" data-panel-body data-actions={actions ? '' : undefined}>
      {@render children()}
    </div>
  </ScrollArea>

  {#if actions}
    <div class="actions">{@render actions()}</div>
  {/if}
</svelte:element>

<style>
  .head {
    display: flex;
    align-items: flex-start;
    gap: var(--spacing-3);
    padding: var(--spacing-inset-panel) var(--spacing-inset-panel) var(--spacing-3);
  }

  /* Focused only by script, to announce the panel; the outline still shows for the keyboard. */
  .title {
    border-radius: var(--radius-tight);
  }

  .title:focus:not(:focus-visible) {
    outline: none;
  }

  .toolbar {
    padding-inline: var(--spacing-inset-panel);
    padding-block-end: var(--spacing-3);
  }

  .panel :global(.body) {
    flex: 1 1 auto;
  }

  .body-inner {
    padding-inline: var(--spacing-inset-panel);
    padding-block: var(--spacing-1) var(--spacing-inset-panel);
  }

  .body-inner[data-actions] {
    padding-block-end: var(--spacing-4);
  }

  /* One leading-aligned row under the content, primary first. */
  .actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--spacing-2);
    padding: var(--spacing-4) var(--spacing-inset-panel) var(--spacing-inset-panel);
  }
</style>
