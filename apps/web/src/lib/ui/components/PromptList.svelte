<script lang="ts">
  // The Prompts tab (workspace look §6.1, F89 to F92): search, the view and tag filters, the
  // sortable header and the rows. Holding Shift turns each row's controls into a delete button.
  import type { Prompt } from '$lib/data';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import PromptRow from './PromptRow.svelte';
  import WorkspaceList, { type ListFilter } from './WorkspaceList.svelte';

  type Props = {
    prompts: Prompt[];
    me?: string;
    onopen?: (id: string) => void;
    ontoggle?: (id: string, active: boolean) => void;
    onclone?: (prompt: Prompt) => void;
    onexport?: (prompt: Prompt) => void;
    ondelete?: (id: string) => void;
  };

  let { prompts, me, onopen, ontoggle, onclone, onexport, ondelete }: Props = $props();

  let query = $state('');
  let view = $state<'all' | 'mine' | 'shared'>('all');
  let tag = $state('');
  let sort = $state<{ by: 'name' | 'updated'; down: boolean }>({ by: 'updated', down: true });
  let deleting = $state<Prompt>();
  let quick = $state(false);

  const VIEWS = { all: 'All', mine: 'Created by you', shared: 'Shared with you' } as const;
  const tags = $derived([...new Set(prompts.flatMap((one) => one.tags))].sort());
  const capital = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);
  const cut = (text: string) => (text.length > 32 ? `${text.slice(0, 32)}...` : text);

  const shown = $derived.by(() => {
    const q = query.trim().toLowerCase();
    const list = prompts.filter(
      (one) =>
        [one.name, one.command, one.content].some((text) => text.toLowerCase().includes(q)) &&
        (!tag || one.tags.includes(tag)) &&
        (view === 'all' || (view === 'mine') === (one.owner?.email === me)),
    );
    const sign = sort.down ? -1 : 1;
    return list.sort((a, b) =>
      sort.by === 'name'
        ? sign * a.name.localeCompare(b.name)
        : sign * (a.updated.getTime() - b.updated.getTime()),
    );
  });

  const filters = $derived<ListFilter[]>([
    {
      id: 'view',
      label: VIEWS[view],
      value: view,
      options: Object.entries(VIEWS).map(([value, label]) => ({ value, label })),
      onChange: (value) => (view = value as typeof view),
      padded: true,
    },
    ...(tags.length
      ? [
          {
            id: 'tag',
            label: tag ? capital(tag) : 'Tag',
            value: tag,
            options: tags.map((one) => ({ value: one, label: cut(capital(one)) })),
            onChange: (value: string) => (tag = value),
            caret: 10,
            clearable: true,
          },
        ]
      : []),
  ]);

  // Shift held anywhere switches every row to quick delete; leaving the window ends it (F91).
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
  searchLabel="Search Prompts"
  bind:query
  bind:sort
  {filters}
  count={shown.length}
  emptyTitle="No prompts found"
>
  {#snippet rows()}
    {#each shown as prompt (prompt.id)}
      <PromptRow
        {prompt}
        {quick}
        {onopen}
        {ontoggle}
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
  title="Delete prompt?"
  message={`This will delete /${deleting?.command ?? ''}`}
  onconfirm={() => {
    if (deleting) ondelete?.(deleting.id);
    deleting = undefined;
  }}
  oncancel={() => (deleting = undefined)}
/>
