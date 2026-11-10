<script lang="ts">
  // People (admin look §4): the Overview and Groups tabs with their counts, beside the content.
  import { page } from '$app/state';
  import { data as source } from '$lib/data';
  import type { AdminUser, Group, StoredPermissions } from '$lib/data';
  import GroupEditor from '$lib/ui/components/GroupEditor.svelte';
  import GroupList from '$lib/ui/components/GroupList.svelte';
  import AccessPreviewDialog from '$lib/ui/components/AccessPreviewDialog.svelte';
  import AddUserDialog from '$lib/ui/components/AddUserDialog.svelte';
  import EditUserDialog from '$lib/ui/components/EditUserDialog.svelte';
  import AdminSection from '$lib/ui/components/AdminSection.svelte';
  import PeopleList from '$lib/ui/components/PeopleList.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();

  let counts = $state<{ people: number; groups: number }>();
  let version = $state(0);
  let adding = $state(false);
  let editing = $state<AdminUser>();
  let previewing = $state<AdminUser>();
  let groupMode = $state<'create' | 'edit' | 'defaults'>();
  let group = $state<Group>();
  let defaults = $state<StoredPermissions>({});
  let removed = $state<Group>();
  const saved = () => {
    adding = false;
    editing = undefined;
    groupMode = undefined;
    version += 1;
  };
  // A group id in the address opens that group's editor (from the person's group chips).
  $effect(() => {
    const id = page.url.searchParams.get('id');
    if (data.tab !== 'groups' || !id) return;
    void source.listGroups().then((all) => {
      const found = all.find((one) => one.id === id);
      if (found) void openGroup('edit', found);
    });
  });
  const openGroup = async (mode: 'create' | 'edit' | 'defaults', chosen?: Group) => {
    defaults = await source.getDefaultPermissions();
    group = chosen;
    groupMode = mode;
  };

  $effect(() => {
    void version;
    void Promise.all([source.listUsers(), source.listGroups()]).then(
      ([people, groups]) => (counts = { people: people.length, groups: groups.length }),
    );
  });
</script>

<AdminSection
  label="People"
  items={[
    {
      href: '/admin/users/overview',
      label: 'Overview',
      count: counts?.people,
      current: data.tab === 'overview',
    },
    {
      href: '/admin/users/groups',
      label: 'Groups',
      count: counts?.groups,
      current: data.tab === 'groups',
    },
  ]}
>
  {#if data.tab === 'overview'}
    <PeopleList
      {source}
      {version}
      onadd={() => (adding = true)}
      onedit={(person) => (editing = person)}
      onpreview={(person) => (previewing = person)}
    />
  {:else}
    {#if removed}
      <p class="undo" role="status">
        Deleted {removed.name}.
        <button
          type="button"
          onclick={async () => {
            if (removed) await source.restoreGroup(removed.id);
            removed = undefined;
            version += 1;
          }}>Undo</button
        >
      </p>
    {/if}
    <GroupList
      {source}
      {version}
      onnew={() => openGroup('create')}
      onedit={(chosen) => openGroup('edit', chosen)}
      ondefaults={() => openGroup('defaults')}
    />
  {/if}
</AdminSection>

{#if groupMode}
  <GroupEditor
    open
    {source}
    mode={groupMode}
    {group}
    {defaults}
    onsaved={saved}
    ondeleted={(gone) => {
      removed = gone;
      saved();
    }}
    onclose={() => (groupMode = undefined)}
  />
{/if}

<AddUserDialog open={adding} {source} onsaved={saved} onclose={() => (adding = false)} />
<EditUserDialog
  open={editing !== undefined}
  {source}
  person={editing}
  selfId={data.user?.id ?? ''}
  onsaved={saved}
  onclose={() => (editing = undefined)}
/>
<AccessPreviewDialog
  open={previewing !== undefined}
  {source}
  person={previewing}
  onclose={() => (previewing = undefined)}
/>

<style>
  .undo {
    display: flex;
    gap: 8px;
    margin-block: 4px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .undo button {
    color: inherit;
    text-decoration: underline;
  }
</style>
