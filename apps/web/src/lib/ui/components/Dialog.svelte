<script lang="ts">
  // A modal dialog, only for real decisions, short forms, stepped flows and re-authentication;
  // everyday tasks open in the side panel. bits-ui supplies the behaviour: focus moves in, stays in,
  // and returns to where it was; Esc closes; the page behind cannot scroll. The look is the shared
  // panel at e3 over a flat scrim, arriving at slow with 8 px of travel.
  //
  // - dismissible={false}: a press on the scrim does nothing; only Esc and the buttons close.
  // - role="alertdialog": a confirmation of something irreversible. Name the consequence in the
  //   description, mark the dismiss button with data-dismiss: focus starts there, Enter is ignored
  //   so a reflex cannot confirm, and the scrim never closes it.
  // - placement="bottom": docked to the bottom edge as a sheet (Sheet.svelte).
  // - Focus starts on an element marked data-autofocus, else the first control in the body, else
  //   the title. The close button is never first.
  import { Dialog } from 'bits-ui';
  import type { Snippet } from 'svelte';
  import IconButton from './IconButton.svelte';
  import Panel from './Panel.svelte';
  import './surfaces.css';

  type Props = {
    open?: boolean;
    title: string;
    description?: string;
    /** The close button's name and hint. */
    closeLabel: string;
    role?: 'dialog' | 'alertdialog';
    dismissible?: boolean;
    size?: 'small' | 'medium' | 'large';
    placement?: 'center' | 'bottom';
    /** Renders the opener, so focus returns to it; spread the props onto a button. */
    trigger?: Snippet<[{ props: Record<string, unknown> }]>;
    children: Snippet;
    /** The actions row: primary first, named by verb and object. */
    actions?: Snippet<[{ close: () => void }]>;
    onOpenChange?: (open: boolean) => void;
  };

  let {
    open = $bindable(false),
    title,
    description,
    closeLabel,
    role = 'dialog',
    dismissible = true,
    size = 'medium',
    placement = 'center',
    trigger,
    children,
    actions,
    onOpenChange,
  }: Props = $props();

  const id = $props.id();
  const alert = $derived(role === 'alertdialog');
  const TABBABLE =
    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), ' +
    'textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

  let panel = $state<HTMLElement>();
  let heading = $state<HTMLElement>();

  const close = () => (open = false);

  function focusStart(event: Event) {
    event.preventDefault();
    const body = panel?.querySelector('[data-panel-body]');
    const target =
      panel?.querySelector<HTMLElement>('[data-autofocus]') ??
      (alert ? panel?.querySelector<HTMLElement>('[data-dismiss]') : null) ??
      body?.querySelector<HTMLElement>(TABBABLE) ??
      heading;
    target?.focus();
  }

  // Enter would press whatever has focus; in a confirmation it must not confirm by reflex.
  function keydown(event: KeyboardEvent) {
    if (!alert || event.key !== 'Enter' || event.isComposing) return;
    if (event.target instanceof HTMLTextAreaElement) return;
    event.preventDefault();
  }
</script>

{#snippet closeButton()}
  <IconButton icon="x" label={closeLabel} shortcut={['esc']} onclick={close} />
{/snippet}

{#snippet panelActions()}
  {@render actions?.({ close })}
{/snippet}

<Dialog.Root bind:open {onOpenChange}>
  {#if trigger}
    <Dialog.Trigger>
      {#snippet child({ props })}
        {@render trigger({ props })}
      {/snippet}
    </Dialog.Trigger>
  {/if}
  <Dialog.Portal>
    <Dialog.Overlay>
      {#snippet child({ props })}
        <div {...props} data-surface="scrim"></div>
      {/snippet}
    </Dialog.Overlay>
    <Dialog.Content
      interactOutsideBehavior={dismissible && !alert ? 'close' : 'ignore'}
      onOpenAutoFocus={focusStart}
      onkeydown={keydown}
    >
      {#snippet child({ props })}
        <Panel
          {...props}
          bind:ref={panel}
          bind:heading
          {role}
          {title}
          {description}
          element="div"
          titleId="{id}-title"
          descriptionId="{id}-description"
          aria-labelledby="{id}-title"
          aria-describedby={description ? `${id}-description` : undefined}
          data-placement={placement}
          data-size={size}
          headerEnd={alert ? undefined : closeButton}
          actions={actions ? panelActions : undefined}
        >
          {@render children()}
        </Panel>
      {/snippet}
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>
