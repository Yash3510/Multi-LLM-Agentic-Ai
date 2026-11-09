<script lang="ts">
  // The Skills tab (workspace look §7.1, F101 to F103): search, the view filter, the sortable
  // header and the rows. Holding Shift turns each row's controls into a delete button.
  import type { Skill } from '$lib/data';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import SkillRow from './SkillRow.svelte';
  import WorkspaceList from './WorkspaceList.svelte';

  type Props = {
    skills: Skill[];
    me?: string;
    onopen?: (id: string) => void;
    ontoggle?: (id: string, active: boolean) => void;
    onclone?: (skill: Skill) => void;
    onexport?: (skill: Skill) => void;
    ondelete?: (id: string) => void;
  };

  let { skills, me, onopen, ontoggle, onclone, onexport, ondelete }: Props = $props();

  let query = $state('');
  let view = $state<'all' | 'mine' | 'shared'>('all');
  let sort = $state<{ by: 'name' | 'updated'; down: boolean }>({ by: 'updated', down: true });
  let deleting = $state<Skill>();
  let quick = $state(false);

  const VIEWS = { all: 'All', mine: 'Created by you', shared: 'Shared with you' } as const;

  const shown = $derived.by(() => {
    const q = query.trim().toLowerCase();
    const list = skills.filter(
      (one) =>
        [one.name, one.id, one.description ?? ''].some((text) => text.toLowerCase().includes(q)) &&
        (view === 'all' || (view === 'mine') === (one.owner?.email === me)),
    );
    const sign = sort.down ? -1 : 1;
    return list.sort((a, b) =>
      sort.by === 'name'
        ? sign * a.name.localeCompare(b.name)
        : sign * (a.updated.getTime() - b.updated.getTime()),
    );
  });

  // Shift held anywhere switches every row to quick delete; leaving the window ends it (F102).
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
  searchLabel="Search Skills"
  bind:query
  bind:sort
  count={shown.length}
  emptyTitle="No skills found"
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
    {#each shown as skill (skill.id)}
      <SkillRow
        {skill}
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
  title="Delete skill?"
  message={`This will delete ${deleting?.name ?? ''}`}
  onconfirm={() => {
    if (deleting) ondelete?.(deleting.id);
    deleting = undefined;
  }}
  oncancel={() => (deleting = undefined)}
/>
