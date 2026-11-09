<script lang="ts">
  // The Tools tab (workspace look §9.1, F108 to F111): search, the view filter, the sortable
  // header and the rows. Holding Shift turns each row's controls into a delete button.
  import type { Tool } from '$lib/data';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import ToolRow from './ToolRow.svelte';
  import ToolSettingsDialog from './ToolSettingsDialog.svelte';
  import WorkspaceList from './WorkspaceList.svelte';

  type Props = {
    tools: Tool[];
    me?: string;
    onopen?: (id: string) => void;
    onclone?: (tool: Tool) => void;
    onexport?: (tool: Tool) => void;
    ondelete?: (id: string) => void;
  };

  let { tools, me, onopen, onclone, onexport, ondelete }: Props = $props();

  let query = $state('');
  let view = $state<'all' | 'mine' | 'shared'>('all');
  let sort = $state<{ by: 'name' | 'updated'; down: boolean }>({ by: 'updated', down: true });
  let deleting = $state<Tool>();
  let settingsFor = $state<Tool>();
  let quick = $state(false);

  const VIEWS = { all: 'All', mine: 'Created by you', shared: 'Shared with you' } as const;

  const shown = $derived.by(() => {
    const q = query.trim().toLowerCase();
    // Name, id and owner match the search (F108).
    const list = tools.filter(
      (one) =>
        [one.name, one.id, one.owner?.name ?? '', one.owner?.email ?? ''].some((text) =>
          text.toLowerCase().includes(q),
        ) &&
        (view === 'all' || (view === 'mine') === (one.owner?.email === me)),
    );
    const sign = sort.down ? -1 : 1;
    return list.sort((a, b) =>
      sort.by === 'name'
        ? sign * a.name.localeCompare(b.name)
        : sign * (a.updated.getTime() - b.updated.getTime()),
    );
  });

  // Shift held anywhere switches every row to quick delete; leaving the window ends it (F110).
  $effect(() => {
    const down = (event: KeyboardEvent) => event.key === 'Shift' && (quick = true);
    const up = (event: KeyboardEvent) => event.key === 'Shift' && (quick = false);
    const blur = () => (quick = false);
    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    window.addEventListener('blur', blur);
    return () => {
      window.removeEventListener('keydown', down);
      window.removeEventListener('keyup', up);
      window.removeEventListener('blur', blur);
    };
  });
</script>

<WorkspaceList
  searchLabel="Search Tools"
  bind:query
  bind:sort
  count={shown.length}
  emptyTitle="No tools found"
  filters={[
    {
      id: 'view',
      label: VIEWS[view],
      value: view,
      options: Object.entries(VIEWS).map(([value, label]) => ({ value, label })),
      onChange: (value) => (view = value as typeof view),
      padded: true,
    },
  ]}
>
  {#snippet rows()}
    {#each shown as tool (tool.id)}
      <ToolRow
        {tool}
        {quick}
        {onopen}
        onsettings={(one) => (settingsFor = one)}
        {onclone}
        {onexport}
        {ondelete}
        onconfirmdelete={(one) => (deleting = one)}
      />
    {/each}
  {/snippet}
</WorkspaceList>

<ConfirmDialog
  open={deleting !== undefined}
  title="Delete tool?"
  message={`This will delete ${deleting?.name ?? ''}`}
  onconfirm={() => {
    if (deleting) ondelete?.(deleting.id);
    deleting = undefined;
  }}
  oncancel={() => (deleting = undefined)}
/>

<ToolSettingsDialog open={settingsFor !== undefined} onclose={() => (settingsFor = undefined)} />
