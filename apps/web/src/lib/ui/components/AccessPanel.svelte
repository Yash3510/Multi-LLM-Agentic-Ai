<script lang="ts">
  // Who can use an item (workspace look §8.1, F10): private or public, then the access list.
  // Shown inline in the create-knowledge dialog and inside the Access dialog.
  import Icon from '$lib/ui/icons/Icon.svelte';

  type Props = {
    visibility?: 'private' | 'public';
    /** Adding people and groups opens the member picker (look §8.3). */
    onadd?: () => void;
  };

  let { visibility = $bindable('private'), onadd }: Props = $props();

  const HELP = {
    private: 'Only select users and groups with permission can access',
    public: 'Accessible to all users',
  } as const;
</script>

<div class="panel">
  <div class="visibility">
    <span class="bubble">
      <Icon
        name={visibility === 'private' ? 'visibility-private' : 'visibility-public'}
        size={20}
      />
    </span>
    <div>
      <span class="choice">
        <select bind:value={visibility} aria-label="Visibility">
          <option value="private">Private</option>
          <option value="public">Public</option>
        </select>
        <!-- The base select's chevron (look §0.5): drawn at 1.5em against the right edge. -->
        <svg class="chevron" viewBox="0 0 24 24" aria-hidden="true"
          ><path d="m6 9 6 6 6-6" fill="none" stroke="currentColor" stroke-width="1.5" /></svg
        >
      </span>
      <p class="help">{HELP[visibility]}</p>
    </div>
  </div>
  <div class="list-head">
    <span>Access List</span>
    <button type="button" class="add" onclick={onadd}>
      <Icon name="plus" size={12} />Add Access
    </button>
  </div>
  <p class="none">No access grants. Private to you.</p>
</div>

<style>
  .panel {
    display: flex;
    flex-direction: column;
    gap: 4px;
    border-radius: 8px;
  }

  .visibility {
    display: flex;
    align-items: center;
    gap: 8px;
    padding-block: 6px;
  }

  .bubble {
    display: grid;
    place-items: center;
    padding: 8px;
    border-radius: var(--radius-pill);
    background-color: rgb(0 0 0 / 0.05);
  }

  :global([data-theme='dark']) .bubble {
    background-color: rgb(255 255 255 / 0.05);
  }

  .choice {
    position: relative;
    display: inline-flex;
    align-items: center;
  }

  select {
    padding-inline-end: 32px;
    appearance: none;
    background: transparent;
    color: inherit;
    font-size: var(--text-ui);
    line-height: 20px;
    cursor: pointer;
  }

  select:focus {
    outline: none;
  }

  option {
    color: var(--color-gray-700);
  }

  .chevron {
    position: absolute;
    inset-inline-end: 0;
    inline-size: 1.5em;
    block-size: 1.5em;
    color: var(--color-select-chevron);
    font-size: var(--text-ui);
    pointer-events: none;
  }

  .help {
    color: var(--color-gray-400);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .list-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-block: 2px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
  }

  .add {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    border-radius: 8px;
    transition: background-color 150ms;
  }

  .add:hover {
    background-color: var(--color-gray-100);
  }

  :global([data-theme='dark']) .add:hover {
    background-color: var(--color-gray-800);
  }

  .none {
    padding-block: 12px;
    color: var(--color-gray-500);
    font-size: var(--text-caption);
    line-height: 16px;
    text-align: center;
  }
</style>
