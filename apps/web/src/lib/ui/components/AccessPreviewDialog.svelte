<script lang="ts">
  // What a person can reach (admin look §10, F50 to F53): their groups, then models, knowledge
  // and tools, reloaded each time the dialog opens.
  import { Dialog } from 'bits-ui';
  import type { AdminUser, DataSource } from '$lib/data';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import './admin-dialog.css';
  import './modal.css';

  type Props = { open: boolean; source: DataSource; person?: AdminUser; onclose: () => void };

  let { open, source, person, onclose }: Props = $props();

  type Access = Awaited<ReturnType<DataSource['previewAccess']>>;
  let access = $state<Access>();
  let failed = $state('');

  $effect(() => {
    if (!open || !person) return;
    access = undefined;
    failed = '';
    source.previewAccess(person.id).then(
      (loaded) => (access = loaded),
      (error: unknown) => (failed = error instanceof Error ? error.message : 'Not available.'),
    );
  });

  const sections = $derived(
    access
      ? ([
          ['Models', access.models, 'No models accessible'],
          ['Knowledge', access.knowledge, 'No knowledge bases accessible'],
          ['Tools', access.tools, 'No tools accessible'],
        ] as const)
      : [],
  );
</script>

<Dialog.Root {open} onOpenChange={(next) => !next && onclose()}>
  <Dialog.Portal>
    <Dialog.Overlay class="modal-backdrop" />
    <Dialog.Content class="modal-frame" aria-describedby={undefined}>
      <div class="admin-dialog medium">
        <div class="head preview-head">
          <Dialog.Title>
            {#snippet child({ props })}
              <h3 {...props} class="title">
                User Preview <span class="who">{person?.name}</span>
              </h3>
            {/snippet}
          </Dialog.Title>
          <Dialog.Close class="bare" aria-label="Close"><Icon name="x" size={16} /></Dialog.Close>
        </div>
        <div class="body">
          {#if failed}
            <p class="failed" role="alert">{failed}</p>
          {:else if !access}
            <p class="loading" aria-busy="true">Loading…</p>
          {:else}
            {#if access.groups.length}
              <section>
                <h4>Groups</h4>
                {#each access.groups as group, at (at)}<p class="item">{group}</p>{/each}
              </section>
              <hr />
            {/if}
            {#each sections as [heading, items, none], index (heading)}
              {#if index}<hr />{/if}
              <section>
                <h4>{heading}</h4>
                {#each items as item, at (at)}<p class="item">{item}</p>{:else}<p class="none">
                    {none}
                  </p>{/each}
              </section>
            {/each}
          {/if}
        </div>
      </div>
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>

<style>
  :global([data-theme='dark']) .preview-head {
    color: var(--color-gray-100);
  }

  .title {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .who {
    margin-inline-start: 4px;
    color: var(--color-gray-500);
    font-weight: 400;
  }

  :global(.bare) {
    display: grid;
    flex-shrink: 0;
  }

  .body {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 0 20px 16px;
  }

  .loading {
    padding-block: 32px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    text-align: center;
  }

  .failed {
    padding-block: 16px;
    color: var(--color-red-500);
    font-size: var(--text-caption);
    text-align: center;
  }

  h4 {
    margin-block-end: 8px;
    font-size: var(--text-ui);
    font-weight: 400;
  }

  .item {
    margin-block: 4px;
    font-size: var(--text-caption);
  }

  .none {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  hr {
    margin-block: 4px;
    border: 0;
    border-block-start: 1px solid var(--color-gray-50);
  }

  :global([data-theme='dark']) hr {
    border-color: color-mix(in srgb, var(--color-gray-850) 30%, transparent);
  }
</style>
