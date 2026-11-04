<script lang="ts">
  // A card in the flow: e0, a line-1 edge on the card radius with the card inset. It becomes one
  // control when it has an href (a link) or an onclick (a button): the whole card is the target, so
  // it holds no other controls, and it rises to e1 on hover, never moving. A button card holds
  // phrasing content only (spans), as any button does.
  //
  // - selected: the card whose detail is open beside it. aria-current on a link, aria-pressed on a
  //   button; drawn with the selected recipe.
  // - disabled: ink-disabled throughout, never opacity. With a reason it stays focusable and the
  //   reason shows under the content, as its description.
  // - loading: aria-busy and no presses; the caller puts skeletons inside.
  // - invalid: a stop edge; the message itself goes inside, in place (InlineAlert).
  import { resolve } from '$app/paths';
  import type { PathnameWithSearchOrHash } from '$app/types';
  import type { Snippet } from 'svelte';
  import type { HTMLAttributes } from 'svelte/elements';
  import './surfaces.css';

  type Props = Omit<HTMLAttributes<HTMLElement>, 'onclick' | 'children'> & {
    /** An in-app path; it gets the base path here. */
    href?: PathnameWithSearchOrHash;
    onclick?: (event: MouseEvent) => void;
    /** Pass it, even as false, on a button card that can be selected: it makes the card a toggle. */
    selected?: boolean;
    disabled?: boolean;
    /** Why it is disabled; keeps it focusable and says so under the content. */
    reason?: string;
    loading?: boolean;
    invalid?: boolean;
    /** The element of a static card. */
    element?: 'div' | 'article' | 'section' | 'li';
    children: Snippet;
  };

  let {
    href,
    onclick,
    selected,
    disabled = false,
    reason,
    loading = false,
    invalid = false,
    element = 'div',
    children,
    class: className,
    'aria-describedby': describedBy,
    ...rest
  }: Props = $props();

  const id = $props.id();
  const kind = $derived(href !== undefined ? 'link' : onclick ? 'button' : 'static');
  const explained = $derived(disabled && !!reason);
  const described = $derived(
    [describedBy, explained ? `${id}-reason` : undefined].filter(Boolean).join(' ') || undefined,
  );

  function click(event: MouseEvent) {
    if (disabled || loading) {
      event.preventDefault();
      return;
    }
    onclick?.(event);
  }
</script>

{#snippet body()}
  {@render children()}
  {#if explained}
    <span id="{id}-reason" class="block text-caption text-ink-3" data-card-reason>{reason}</span>
  {/if}
{/snippet}

{#if kind === 'link'}
  <!-- A disabled link has no href, so it goes nowhere; with a reason it stays in the tab order. -->
  <a
    {...rest}
    href={disabled || href === undefined ? undefined : resolve(href)}
    role={disabled ? 'link' : undefined}
    tabindex={disabled ? (explained ? 0 : -1) : undefined}
    class={className}
    data-surface="card"
    data-interactive=""
    data-invalid={invalid || undefined}
    data-disabled={disabled || undefined}
    aria-current={selected ? 'true' : undefined}
    aria-disabled={disabled ? 'true' : undefined}
    aria-busy={loading ? 'true' : undefined}
    aria-describedby={described}
    onclick={click}
  >
    {@render body()}
  </a>
{:else if kind === 'button'}
  <button
    {...rest}
    type="button"
    class={className}
    disabled={disabled && !explained}
    data-surface="card"
    data-interactive=""
    data-invalid={invalid || undefined}
    data-disabled={disabled || undefined}
    aria-pressed={selected}
    aria-disabled={explained ? 'true' : undefined}
    aria-busy={loading ? 'true' : undefined}
    aria-describedby={described}
    onclick={click}
  >
    {@render body()}
  </button>
{:else}
  <svelte:element
    this={element}
    {...rest}
    class={className}
    data-surface="card"
    data-invalid={invalid || undefined}
    data-disabled={disabled || undefined}
    aria-busy={loading ? 'true' : undefined}
    aria-describedby={described}
  >
    {@render body()}
  </svelte:element>
{/if}
