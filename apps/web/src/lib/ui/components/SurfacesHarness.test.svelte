<script lang="ts">
  // Test-only: the layered surfaces with their openers, so surfaces.test.ts can check focus.
  import Dialog from './Dialog.svelte';
  import Disclosure from './Disclosure.svelte';
  import SidePanel from './SidePanel.svelte';

  type Props = {
    kind: 'dialog' | 'confirm' | 'dock' | 'disclosure';
    onconfirm?: () => void;
  };

  let { kind, onconfirm }: Props = $props();
  let open = $state(false);
</script>

{#if kind === 'dialog'}
  <Dialog title="Rename CASE-0142" closeLabel="Close">
    {#snippet trigger({ props })}
      <button {...props}>Rename case</button>
    {/snippet}
    <label>Name <input data-autofocus /></label>
    {#snippet actions({ close })}
      <button onclick={close}>Cancel</button>
    {/snippet}
  </Dialog>
{:else if kind === 'confirm'}
  <Dialog
    role="alertdialog"
    title="Delete 3 drafts?"
    description="They are removed for everyone and cannot be restored."
    closeLabel="Close"
  >
    {#snippet trigger({ props })}
      <button {...props}>Delete drafts</button>
    {/snippet}
    <p>R2, R3 and R4.</p>
    {#snippet actions({ close })}
      <button onclick={onconfirm}>Delete 3 drafts</button>
      <button data-dismiss onclick={close}>Keep drafts</button>
    {/snippet}
  </Dialog>
{:else if kind === 'dock'}
  <div>
    <button onclick={() => (open = true)}>Open CASE-0142</button>
    <button>Another page control</button>
    <SidePanel bind:open title="CASE-0142" closeLabel="Close panel">
      <p>Ratio 82.5 %</p>
    </SidePanel>
  </div>
{:else}
  <Disclosure label="Show the inputs" detail="3 inputs">
    <button>Inside</button>
  </Disclosure>
{/if}
