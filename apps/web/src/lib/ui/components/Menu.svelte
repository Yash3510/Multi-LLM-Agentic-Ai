<script lang="ts">
  // A dropdown menu of commands and choices (bits-ui behaviour): arrow keys move, Home and End jump,
  // typing a letter finds a row, Enter or Space chooses, Esc closes and focus returns to the trigger.
  // Rows have an icon and a word, and shortcuts as key caps. e2 on the card radius.
  //
  // Nested choices never open a flyout: their row drills in, so the same panel shows the nested rows
  // under a back row. Right arrow or a press goes in; left arrow or the back row comes out, back to
  // the row it came from. Every opening starts at the top. Disabled rows say why under the label.
  import { DropdownMenu } from 'bits-ui';
  import { tick, type Snippet } from 'svelte';
  import type { IconName } from '$lib/ui/icons/generated/icons';
  import { glide } from '$lib/ui/glide';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import type { ActionSize } from './ActionBase.svelte';
  import Kbd from './Kbd.svelte';
  import { ariaShortcut, isApple } from './keycap';
  import {
    drillHint,
    hasIcons,
    levelAt,
    type MenuAction,
    type MenuChoices,
    type MenuDrill,
    type MenuEntry,
  } from './menu-model';
  import './actions.css';
  import './glide.css';
  import './menu.css';
  import './surfaces.css';

  type Props = {
    /** The trigger's word, also the menu's name. */
    label: string;
    icon?: IconName;
    variant?: 'primary' | 'secondary' | 'quiet';
    size?: ActionSize;
    items: MenuEntry[];
    /** Read before the level's name on the back row, e.g. "Back". */
    backLabel: string;
    align?: 'start' | 'end';
    /** A custom trigger instead of the button: spread the props onto a button. */
    trigger?: Snippet<[{ props: Record<string, unknown> }]>;
    disabled?: boolean;
    open?: boolean;
  };

  let {
    label,
    icon,
    variant = 'secondary',
    size = 'ui',
    items,
    backLabel,
    align = 'start',
    trigger,
    disabled = false,
    open = $bindable(false),
  }: Props = $props();

  const id = $props.id();
  const apple = isApple();

  let path = $state<string[]>([]);
  const level = $derived(levelAt(items, path));
  const parent = $derived(level.trail.at(-1));
  const iconColumn = $derived(hasIcons(level.entries));

  let content = $state<HTMLElement | null>(null);
  /** The last input was a key: the highlighted row then shows the focus outline, not hover. */
  let keyboard = $state(false);

  function openChange(next: boolean) {
    if (next) path = [];
  }

  /** After a level change: the pointer leaves focus on the panel, the keyboard gets a row. */
  async function focusRow(pick: (rows: HTMLElement[]) => HTMLElement | undefined) {
    await tick();
    if (!content) return;
    const rows = [...content.querySelectorAll<HTMLElement>('[data-menu-row]:not([data-disabled])')];
    const row = keyboard ? pick(rows) : undefined;
    (row ?? content).focus();
  }

  function enter(drill: MenuDrill) {
    if (drill.disabled) return;
    path = [...level.trail.map((step) => step.id), drill.id];
    focusRow((rows) => rows.find((row) => !row.hasAttribute('data-back')));
  }

  function back() {
    const from = parent?.id;
    if (!from) return;
    path = path.slice(0, -1);
    focusRow((rows) => rows.find((row) => row.dataset.drill === from) ?? rows[0]);
  }

  function contentKeydown(event: KeyboardEvent) {
    if (event.key === 'ArrowLeft' && parent) {
      event.preventDefault();
      back();
    }
  }

  function drillKeydown(event: KeyboardEvent, drill: MenuDrill) {
    if (event.key === 'ArrowRight') {
      event.preventDefault();
      enter(drill);
    }
  }
</script>

<svelte:document onkeydown={() => (keyboard = true)} onpointermove={() => (keyboard = false)} />

{#snippet lead(name: IconName | undefined)}
  {#if iconColumn}
    <span data-menu-lead
      >{#if name}<Icon {name} size={14} />{/if}</span
    >
  {/if}
{/snippet}

{#snippet action(entry: MenuAction)}
  {@const reasonId = entry.disabled && entry.reason ? `${id}-${entry.id}-reason` : undefined}
  <DropdownMenu.Item
    disabled={entry.disabled}
    textValue={entry.label}
    onSelect={() => entry.onSelect?.()}
    aria-keyshortcuts={entry.shortcut?.length ? ariaShortcut(entry.shortcut, apple) : undefined}
    aria-describedby={reasonId}
  >
    {#snippet child({ props })}
      <div {...props} data-menu-row data-danger={entry.danger || undefined}>
        {@render lead(entry.icon)}
        <span data-menu-text>
          <span data-menu-label>{entry.label}</span>
          {#if reasonId}<span id={reasonId} data-menu-reason>{entry.reason}</span>{/if}
        </span>
        {#if entry.shortcut?.length}
          <!-- aria-keyshortcuts says it, so the caps are not read twice. -->
          <Kbd keys={entry.shortcut} aria-hidden="true" />
        {/if}
      </div>
    {/snippet}
  </DropdownMenu.Item>
{/snippet}

{#snippet drill(entry: MenuDrill)}
  {@const hint = drillHint(entry)}
  <DropdownMenu.Item
    disabled={entry.disabled}
    textValue={entry.label}
    closeOnSelect={false}
    onSelect={() => enter(entry)}
    onkeydown={(event: KeyboardEvent) => drillKeydown(event, entry)}
  >
    {#snippet child({ props })}
      <div {...props} data-menu-row data-drill={entry.id}>
        {@render lead(entry.icon)}
        <span data-menu-text><span data-menu-label>{entry.label}</span></span>
        {#if hint}<span data-menu-hint>{hint}</span>{/if}
        <span data-menu-trail><Icon name="caret-right" size={14} /></span>
      </div>
    {/snippet}
  </DropdownMenu.Item>
{/snippet}

{#snippet choices(entry: MenuChoices)}
  <DropdownMenu.RadioGroup
    value={entry.value}
    onValueChange={entry.onChange}
    aria-label={entry.label}
  >
    {#each entry.options as option (option.value)}
      <DropdownMenu.RadioItem
        value={option.value}
        disabled={option.disabled}
        textValue={option.label}
      >
        {#snippet child({ props, checked })}
          <div {...props} data-menu-row data-checked={checked || undefined}>
            {@render lead(option.icon)}
            <span data-menu-text><span data-menu-label>{option.label}</span></span>
            <span data-menu-trail
              >{#if checked}<Icon name="check" size={14} />{/if}</span
            >
          </div>
        {/snippet}
      </DropdownMenu.RadioItem>
    {/each}
  </DropdownMenu.RadioGroup>
{/snippet}

{#snippet entryRow(entry: MenuEntry)}
  {#if entry.type === 'separator'}
    <DropdownMenu.Separator>
      {#snippet child({ props })}<div {...props} data-menu-separator></div>{/snippet}
    </DropdownMenu.Separator>
  {:else if entry.type === 'drill'}
    {@render drill(entry)}
  {:else if entry.type === 'choices'}
    {@render choices(entry)}
  {:else if entry.type === 'group'}
    <DropdownMenu.Group>
      {#snippet child({ props })}
        <div {...props}>
          <DropdownMenu.GroupHeading>
            {#snippet child({ props: headingProps })}
              <div {...headingProps} data-menu-heading>{entry.label}</div>
            {/snippet}
          </DropdownMenu.GroupHeading>
          {#each entry.items as item, index (item.type === 'separator' ? `sep-${index}` : item.id)}
            {@render entryRow(item)}
          {/each}
        </div>
      {/snippet}
    </DropdownMenu.Group>
  {:else}
    {@render action(entry)}
  {/if}
{/snippet}

<DropdownMenu.Root bind:open onOpenChange={openChange}>
  <DropdownMenu.Trigger {disabled}>
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
          {#if icon}<Icon name={icon} size={14} />{/if}
          <span>{label}</span>
          <Icon name="caret-down" size={12} />
        </button>
      {/if}
    {/snippet}
  </DropdownMenu.Trigger>
  <DropdownMenu.Portal>
    <DropdownMenu.Content
      bind:ref={content}
      {align}
      sideOffset={6}
      collisionPadding={8}
      loop
      onkeydown={contentKeydown}
    >
      {#snippet child({ wrapperProps, props })}
        <div {...wrapperProps}>
          <div
            {...props}
            aria-label={parent ? parent.label : label}
            class="focus-inset"
            data-menu
            data-surface="float"
            data-keyboard={keyboard || undefined}
            {@attach glide({ active: '[data-menu-row][data-highlighted]' })}
          >
            {#if parent}
              <DropdownMenu.Item textValue={parent.label} closeOnSelect={false} onSelect={back}>
                {#snippet child({ props: rowProps })}
                  <div {...rowProps} data-menu-row data-back>
                    <span data-menu-lead><Icon name="caret-left" size={14} /></span>
                    <span data-menu-text>
                      <span data-menu-label
                        ><span class="sr-only">{backLabel}: </span>{parent.label}</span
                      >
                    </span>
                  </div>
                {/snippet}
              </DropdownMenu.Item>
              <div role="separator" data-menu-separator></div>
            {/if}
            {#each level.entries as entry, index (entry.type === 'separator' ? `sep-${index}` : entry.id)}
              {@render entryRow(entry)}
            {/each}
          </div>
        </div>
      {/snippet}
    </DropdownMenu.Content>
  </DropdownMenu.Portal>
</DropdownMenu.Root>
