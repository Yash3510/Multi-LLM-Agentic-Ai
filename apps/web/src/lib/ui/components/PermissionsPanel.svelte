<script lang="ts">
  // The permissions tab (admin look §12d, F74 to F83): switches under six headings, nested rows
  // while their parent is on, and the note when a switch is off here but on by default.
  import type { StoredPermissions } from '$lib/data';
  import {
    type Category,
    type PermissionRow,
    type Permissions,
    SECTIONS,
    visibleRows,
  } from '$lib/ui/permissions';
  import Switch from './Switch.svelte';

  type Props = {
    permissions: Permissions;
    /** The default permissions, for the stays-enabled note; none in defaults mode. */
    defaults?: StoredPermissions;
  };

  let { permissions = $bindable(), defaults }: Props = $props();

  const isDefault = (category: Category, key: string) => defaults?.[category]?.[key] === true;
  const set = (category: Category, key: string, on: boolean) =>
    (permissions = { ...permissions, [category]: { ...permissions[category], [key]: on } });
</script>

{#snippet line(category: Category, row: PermissionRow, child = false)}
  <div class="line" class:child title={row.warn}>
    <span>{row.label}</span>
    <Switch
      on={permissions[category][row.key]}
      label={row.label}
      onchange={(on) => set(category, row.key, on)}
    />
  </div>
{/snippet}

<div class="panel">
  {#each SECTIONS as section, index (section.heading)}
    {#if index}<div class="rule"></div>{/if}
    <section>
      <h4>{section.heading}</h4>
      {#each visibleRows(section, permissions) as row (row.key)}
        <div class="item">
          {@render line(section.category, row)}
          {#if row.children && permissions[section.category][row.key]}
            <div class="children">
              {#each row.children as child (child.key)}
                {@render line(section.category, child, true)}
              {/each}
            </div>
          {:else if isDefault(section.category, row.key) && !permissions[section.category][row.key]}
            <p class="hint">This is a default user permission and will remain enabled.</p>
          {/if}
        </div>
      {/each}
    </section>
  {/each}
</div>

<style>
  .panel {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  h4 {
    margin-block-end: 8px;
    font-size: var(--text-ui);
    font-weight: 400;
    line-height: 20px;
  }

  .item {
    display: flex;
    flex-direction: column;
  }

  .line {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-block: 4px;
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .children {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-inline-start: 8px;
    padding-block: 2px 4px;
  }

  .line.child {
    margin-block: 0;
  }

  .hint {
    padding-block-end: 2px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .rule {
    block-size: 1px;
    background-color: color-mix(in srgb, var(--color-gray-100) 30%, transparent);
  }

  :global([data-theme='dark']) .rule {
    background-color: color-mix(in srgb, var(--color-gray-850) 30%, transparent);
  }
</style>
