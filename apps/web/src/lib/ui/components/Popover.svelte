<script lang="ts">
  // A small layer of detail anchored to its trigger: a peek at a case, the inputs behind a figure.
  // e2 on the card radius, arriving at calm with 4 px of travel from the trigger.
  //
  // Three ways in, so hover is never the only one:
  // - hover: opens after 280 ms of intent and closes 160 ms after the pointer leaves, unless the
  //   pointer crossed onto it. It never takes focus.
  // - keyboard focus on the trigger opens it as a peek, leaving focus where it is; Tab moves on and
  //   closes it. Enter, Space or Down arrow then steps into it.
  // - a press opens it for real: focus moves in and stays in until Esc or a press outside, then
  //   returns to the trigger.
  // Esc always closes it.
  import { Popover } from 'bits-ui';
  import { tick, type Snippet } from 'svelte';
  import type { IconName } from '$lib/ui/icons/generated/icons';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import type { ActionSize } from './ActionBase.svelte';
  import { GRACE_MS, INTENT_MS } from './hover-intent';
  import './actions.css';
  import './surfaces.css';

  type Props = {
    /** The trigger's word. Also names the popover when it has no title. */
    label: string;
    icon?: IconName;
    variant?: 'primary' | 'secondary' | 'quiet';
    size?: ActionSize;
    /** A custom trigger instead of the button: spread the props onto a focusable element. */
    trigger?: Snippet<[{ props: Record<string, unknown> }]>;
    /** A heading inside, which also names it. */
    title?: string;
    children: Snippet;
    side?: 'top' | 'bottom' | 'left' | 'right';
    align?: 'start' | 'center' | 'end';
    /** Open on hover intent and on keyboard focus. Off for popovers that only a press should open. */
    peek?: boolean;
    disabled?: boolean;
    open?: boolean;
  };

  let {
    label,
    icon,
    variant = 'secondary',
    size = 'ui',
    trigger,
    title,
    children,
    side = 'bottom',
    align = 'start',
    peek = true,
    disabled = false,
    open = $bindable(false),
  }: Props = $props();

  const id = $props.id();
  const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), [tabindex="0"]';

  /** How it was opened: a peek (focus) and hover leave focus alone; interactive takes it. */
  let mode = $state<'peek' | 'hover' | 'interactive'>('interactive');
  let content = $state<HTMLElement | null>(null);

  function focusin(event: FocusEvent) {
    if (!peek || open || disabled) return;
    // Only keyboard focus peeks; a press is handled as a press.
    if (!(event.currentTarget as HTMLElement).matches(':focus-visible')) return;
    mode = 'peek';
    open = true;
  }

  function focusout(event: FocusEvent) {
    if (!open || mode !== 'peek') return;
    const next = event.relatedTarget as Node | null;
    if (next && content?.contains(next)) return;
    open = false;
  }

  function pointerenter() {
    if (!open) mode = 'hover';
  }

  async function stepIn() {
    mode = 'interactive';
    await tick();
    (content?.querySelector<HTMLElement>(FOCUSABLE) ?? content)?.focus();
  }

  function keydown(event: KeyboardEvent) {
    if (!open || mode !== 'peek') return;
    if (event.key !== 'Enter' && event.key !== ' ' && event.key !== 'ArrowDown') return;
    // Stops bits-ui's toggle, which would close it.
    event.preventDefault();
    stepIn();
  }

  function click(event: MouseEvent) {
    if (open && mode === 'peek') {
      event.preventDefault();
      stepIn();
      return;
    }
    // Pressing a hover-opened popover keeps it open and makes it interactive (bits-ui converts it).
    mode = 'interactive';
  }

  // Hover and peeks never move focus, in or back out.
  const keepFocus = (event: Event) => {
    if (mode !== 'interactive') event.preventDefault();
  };
</script>

<Popover.Root bind:open>
  <Popover.Trigger
    {disabled}
    openOnHover={peek}
    openDelay={INTENT_MS}
    closeDelay={GRACE_MS}
    onfocus={focusin}
    onblur={focusout}
    onpointerenter={pointerenter}
    onkeydown={keydown}
    onclick={click}
  >
    {#snippet child({ props })}
      {#if trigger}
        {@render trigger({ props })}
      {:else}
        <button
          {...props}
          type="button"
          class={[size === 'small' ? 'text-small' : 'text-ui', 'font-medium']}
          data-action="button"
          data-variant={variant}
          data-size={size}
          data-lead={icon ? '' : undefined}
          data-trail=""
          data-layer-trigger
        >
          {#if icon}<Icon name={icon} size={16} />{/if}
          <span>{label}</span>
          <Icon name="caret-down" size={12} />
        </button>
      {/if}
    {/snippet}
  </Popover.Trigger>
  <Popover.Portal>
    <Popover.Content
      bind:ref={content}
      {side}
      {align}
      sideOffset={6}
      collisionPadding={8}
      trapFocus={mode === 'interactive'}
      onOpenAutoFocus={keepFocus}
      onCloseAutoFocus={keepFocus}
    >
      {#snippet child({ wrapperProps, props })}
        <div {...wrapperProps}>
          <div
            {...props}
            role="dialog"
            aria-labelledby={title ? `${id}-title` : undefined}
            aria-label={title ? undefined : label}
            class="popover focus-inset"
            data-surface="float"
          >
            {#if title}
              <p id="{id}-title" class="text-ui font-medium text-ink-1">{title}</p>
            {/if}
            {@render children()}
          </div>
        </div>
      {/snippet}
    </Popover.Content>
  </Popover.Portal>
</Popover.Root>

<style>
  .popover {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
    inline-size: max-content;
    max-inline-size: min(calc(var(--spacing-12) * 7), var(--bits-popover-content-available-width));
    padding: var(--spacing-inset-card);
    outline-offset: -2px;
  }
</style>
