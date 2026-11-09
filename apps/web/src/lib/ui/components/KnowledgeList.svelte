<script lang="ts">
  // The Knowledge tab (workspace look §4.1 to §4.3): search, the view and source filters, the
  // sortable header and the rows. Deleting asks first.
  import type { KnowledgeBase } from '$lib/data';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import KnowledgeRow from './KnowledgeRow.svelte';
  import WorkspaceList from './WorkspaceList.svelte';

  type Props = {
    bases: KnowledgeBase[];
    /** The signed-in person's email, for "Created by you". */
    me?: string;
    admin?: boolean;
    onopen?: (id: string) => void;
    ondelete?: (id: string) => void;
  };

  let { bases, me, admin = false, onopen, ondelete }: Props = $props();

  let query = $state('');
  let view = $state<'all' | 'mine' | 'shared'>('all');
  let source = $state<'local' | 'connected' | undefined>();
  let sort = $state<{ by: 'name' | 'updated'; down: boolean }>({ by: 'updated', down: true });
  let deleting = $state<string>();

  const VIEWS = { all: 'All', mine: 'Created by you', shared: 'Shared with you' } as const;
  const SOURCES = { local: 'Local', connected: 'Connected' } as const;

  const shown = $derived.by(() => {
    const q = query.trim().toLowerCase();
    const list = bases.filter(
      (base) =>
        base.name.toLowerCase().includes(q) &&
        (!source || base.source === source) &&
        (view === 'all' || (view === 'mine') === (base.owner?.email === me)),
    );
    const sign = sort.down ? -1 : 1;
    return list.sort((a, b) =>
      sort.by === 'name'
        ? sign * a.name.localeCompare(b.name)
        : sign * (a.updated.getTime() - b.updated.getTime()),
    );
  });
</script>

<WorkspaceList
  searchLabel="Search Knowledge"
  bind:query
  bind:sort
  count={shown.length}
  emptyTitle="No knowledge found"
  filters={[
    {
      id: 'view',
      label: VIEWS[view],
      value: view,
      options: Object.entries(VIEWS).map(([value, label]) => ({ value, label })),
      onChange: (value) => (view = value as typeof view),
      padded: true,
    },
    {
      id: 'source',
      label: source ? SOURCES[source] : 'All Sources',
      value: source ?? '',
      options: [
        { value: '', label: 'All Sources' },
        ...Object.entries(SOURCES).map(([value, label]) => ({ value, label })),
      ],
      onChange: (value) => (source = (value || undefined) as typeof source),
      caret: 10,
      clearable: true,
    },
  ]}
>
  {#snippet rows()}
    {#each shown as base (base.id)}
      <KnowledgeRow {base} {admin} {onopen} ondelete={(id) => (deleting = id)} />
    {/each}
  {/snippet}
</WorkspaceList>

<ConfirmDialog
  open={deleting !== undefined}
  title="Are you sure?"
  onconfirm={() => {
    if (deleting) ondelete?.(deleting);
    deleting = undefined;
  }}
  oncancel={() => (deleting = undefined)}
/>
