<script lang="ts">
  // One admin settings panel drawn from its schema (admin look §19, P1 to P4): sections of rows
  // and fields with switches, selects, inputs, text areas, secret fields and text actions. Values
  // start from the schema's defaults overlaid with the stored ones; Save stores them all.
  import { toast } from '$lib/ui/toast.svelte';
  import type { DataSource } from '$lib/data';
  import {
    type Item,
    type Panel,
    type Values,
    panelDefaults,
    shownItems,
  } from '$lib/ui/admin-panels';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import type { ParamValue } from '$lib/ui/params';
  import AdvancedParams from './AdvancedParams.svelte';
  import { SECTIONS as INTERFACE_SECTIONS } from '$lib/ui/interface-prefs';
  import SettingsSelect from './SettingsSelect.svelte';
  import Switch from './Switch.svelte';
  import './settings-page.css';

  type Props = {
    source: DataSource;
    panel: Panel;
    /** Extra select options by key, such as groups for Default Group. */
    choices?: Record<string, [string, string][]>;
    /** An action row was pressed. */
    onaction?: (key: string) => void;
  };

  let { source, panel, choices = {}, onaction }: Props = $props();

  let values = $state<Values>();
  let shown = $state<Record<string, boolean>>({});
  let opened = $state<Record<string, boolean>>({});
  let arenaName = $state('');
  let arenaModels = $state<string[]>([]);
  let arenaOpen = $state(false);
  type Banner = { type: string; content: string; dismissible: boolean };
  const list = <T,>(key?: string) => (values?.[key ?? ''] ?? []) as T[];
  const map = (key?: string) => (values?.[key ?? ''] ?? {}) as Record<string, boolean>;
  const INTERFACE_SWITCHES = INTERFACE_SECTIONS.flatMap((section) =>
    section.rows.filter((row) => row.kind === 'switch'),
  );

  async function uploadWorkflow(
    key: string | undefined,
    event: Event & { currentTarget: HTMLInputElement },
  ) {
    const file = event.currentTarget.files?.[0];
    event.currentTarget.value = '';
    if (!file) return;
    const text = await file.text();
    try {
      JSON.parse(text);
      set(key, text);
    } catch {
      notice = 'That file is not a ComfyUI workflow.';
    }
  }
  let notice = $state('');

  $effect(() => {
    const current = panel;
    values = undefined;
    void source
      .getAdminSettings(current.id)
      .then((stored) => (values = { ...panelDefaults(current), ...stored }));
  });

  const options = (item: Item) => [...(item.options ?? []), ...(choices[item.key ?? ''] ?? [])];
  const set = (key: string | undefined, value: unknown) => {
    if (key && values) values = { ...values, [key]: value };
  };
  const text = (key: string | undefined) => String(values?.[key ?? ''] ?? '');

  async function save(event: SubmitEvent) {
    event.preventDefault();
    if (!values) return;
    await source.saveAdminSettings(panel.id, $state.snapshot(values));
    toast('Settings saved successfully!');
  }
</script>

<form class="settings-page admin-panel" onsubmit={save}>
  <div class="body">
    <h2>{panel.title}</h2>
    {#if values}
      {#each panel.sections.filter((one) => shownItems(one, values ?? {}).length) as section, index (index)}
        <section>
          {#if section.heading}<h3 class="heading">{section.heading}</h3>{/if}
          <div class="rows grouped">
            {#each shownItems(section, values) as item (item.key ?? item.label)}
              {#if item.kind === 'info'}
                <div class="info cell">
                  <span class="label" class:muted={item.muted}>{item.label}</span>
                  {#if item.value}<span class="value">{item.value}</span>{/if}
                  {#if item.note}<p class="note info-note">{item.note}</p>{/if}
                </div>
              {:else if item.kind === 'interface-defaults'}
                <div class="cell">
                  <div class="row params-row">
                    <span>{item.label}</span>
                    <button
                      type="button"
                      class="quiet small"
                      onclick={() =>
                        (opened = { ...opened, [item.key ?? '']: !opened[item.key ?? ''] })}
                      >{opened[item.key ?? ''] ? 'Close' : 'Configure'}</button
                    >
                  </div>
                  {#if item.note}<p class="note">{item.note}</p>{/if}
                  {#if opened[item.key ?? '']}
                    <p class="note">
                      {Object.keys(map(item.key)).length} settings configured
                      {#if Object.keys(map(item.key)).length}<button
                          type="button"
                          class="quiet small"
                          onclick={() => set(item.key, {})}>Clear</button
                        >{/if}
                    </p>
                    <div class="defaults-box">
                      {#each INTERFACE_SWITCHES as row (row.key)}
                        <div class="row">
                          <span>{row.label}</span>
                          <Switch
                            on={map(item.key)[row.key] ?? row.start === true}
                            label={row.label}
                            onchange={(next) =>
                              set(item.key, { ...map(item.key), [row.key]: next })}
                          />
                        </div>
                      {/each}
                    </div>
                  {/if}
                </div>
              {:else if item.kind === 'banners'}
                <div class="cell">
                  <div class="row">
                    <span>{item.label}</span>
                    <button
                      type="button"
                      class="round"
                      aria-label="Add banner"
                      onclick={() =>
                        set(item.key, [
                          ...list<Banner>(item.key),
                          { type: 'info', content: '', dismissible: true },
                        ])}><Icon name="plus" size={16} /></button
                    >
                  </div>
                  {#if item.note}<p class="note">{item.note}</p>{/if}
                  {#each list<Banner>(item.key) as banner, at (at)}
                    <div class="banner">
                      <SettingsSelect
                        label="Banner type"
                        value={banner.type}
                        options={['info', 'warning', 'error', 'success'].map((one) => ({
                          value: one,
                          label: one.charAt(0).toUpperCase() + one.slice(1),
                        }))}
                        onchange={(value) =>
                          set(
                            item.key,
                            list<Banner>(item.key).map((one, i) =>
                              i === at ? { ...one, type: value } : one,
                            ),
                          )}
                      />
                      <textarea
                        class="area"
                        rows="1"
                        aria-label="Banner text"
                        value={banner.content}
                        oninput={(e) =>
                          set(
                            item.key,
                            list<Banner>(item.key).map((one, i) =>
                              i === at ? { ...one, content: e.currentTarget.value } : one,
                            ),
                          )}></textarea>
                      <span title="Remember Dismissal"
                        ><Switch
                          on={banner.dismissible}
                          label="Remember Dismissal"
                          onchange={(next) =>
                            set(
                              item.key,
                              list<Banner>(item.key).map((one, i) =>
                                i === at ? { ...one, dismissible: next } : one,
                              ),
                            )}
                        /></span
                      >
                      <button
                        type="button"
                        class="round"
                        aria-label="Remove banner"
                        onclick={() =>
                          set(
                            item.key,
                            list<Banner>(item.key).filter((_, i) => i !== at),
                          )}><Icon name="x" size={16} /></button
                      >
                    </div>
                  {/each}
                </div>
              {:else if item.kind === 'arena'}
                <div class="cell">
                  <div class="row">
                    <span>{item.label}</span>
                    <button
                      type="button"
                      class="round"
                      aria-label="Add Arena Model"
                      title="Add Arena Model"
                      onclick={() => (arenaOpen = !arenaOpen)}
                      ><Icon name="plus" size={16} /></button
                    >
                  </div>
                  {#if arenaOpen}
                    <div class="arena-form">
                      <input
                        class="input"
                        bind:value={arenaName}
                        placeholder="Arena model name"
                        aria-label="Arena model name"
                      />
                      {#each choices.TASK_MODEL ?? [] as [id, label] (id)}
                        <label class="check"
                          ><input
                            type="checkbox"
                            checked={arenaModels.includes(id)}
                            onchange={(e) =>
                              (arenaModels = e.currentTarget.checked
                                ? [...arenaModels, id]
                                : arenaModels.filter((one) => one !== id))}
                          />{label}</label
                        >
                      {/each}
                      <button
                        type="button"
                        class="quiet"
                        onclick={() => {
                          if (!arenaName.trim()) return;
                          set(item.key, [
                            ...list<{ name: string; models: string[] }>(item.key),
                            { name: arenaName.trim(), models: arenaModels },
                          ]);
                          arenaName = '';
                          arenaModels = [];
                          arenaOpen = false;
                        }}>Add</button
                      >
                    </div>
                  {/if}
                  {#each list<{ name: string; models: string[] }>(item.key) as model, at (at)}
                    <div class="row arena-row">
                      <span
                        >{model.name} <span class="unit">{model.models.length} models</span></span
                      >
                      <button
                        type="button"
                        class="quiet small"
                        onclick={() =>
                          set(
                            item.key,
                            list(item.key).filter((_, i) => i !== at),
                          )}>Remove</button
                      >
                    </div>
                  {:else}
                    <p class="note">No arena models yet.</p>
                  {/each}
                </div>
              {:else if item.kind === 'workflow'}
                <div class="block">
                  <div class="row tall">
                    <span>{item.label}</span>
                    <span class="workflow-actions">
                      <label class="quiet"
                        >Upload<input
                          type="file"
                          accept=".json"
                          hidden
                          aria-label="Workflow file"
                          onchange={(e) => uploadWorkflow(item.key, e)}
                        /></label
                      >
                      {#if values[item.key ?? '']}<button
                          type="button"
                          class="quiet"
                          onclick={() => set(item.key, '')}>Reset</button
                        >{/if}
                    </span>
                  </div>
                  {#if item.note}<p class="note">{item.note}</p>{/if}
                </div>
              {:else if item.kind === 'params'}
                <div class="cell">
                  <div class="row params-row">
                    <span>{item.label}</span>
                    <button
                      type="button"
                      class="quiet small"
                      onclick={() =>
                        (opened = { ...opened, [item.key ?? '']: !opened[item.key ?? ''] })}
                      >{opened[item.key ?? ''] ? 'Close' : 'Configure'}</button
                    >
                  </div>
                  {#if opened[item.key ?? '']}
                    <div class="params-box">
                      <AdvancedParams
                        bind:params={
                          () => (values?.[item.key ?? ''] ?? {}) as Record<string, ParamValue>,
                          (next) => set(item.key, next)
                        }
                        admin
                      />
                    </div>
                  {/if}
                </div>
              {:else if item.field}
                <div class="cell" class:half={item.half}>
                  <label class="field-label" for="admin-{item.key}">{item.label}</label>
                  <div class="field-control">
                    {#if item.kind === 'textarea'}
                      <textarea
                        id="admin-{item.key}"
                        class="area"
                        rows="1"
                        placeholder={item.placeholder}
                        value={text(item.key)}
                        oninput={(event) => set(item.key, event.currentTarget.value)}></textarea>
                    {:else if item.kind === 'select'}
                      <SettingsSelect
                        label={item.label}
                        value={text(item.key)}
                        options={options(item).map(([value, label]) => ({ value, label }))}
                        onchange={(value) => set(item.key, value)}
                        wide
                      />
                    {:else if item.kind === 'secret'}
                      <span class="secret">
                        <input
                          id="admin-{item.key}"
                          type={shown[item.key ?? ''] ? 'text' : 'password'}
                          autocomplete="off"
                          placeholder={item.placeholder}
                          value={text(item.key)}
                          oninput={(event) => set(item.key, event.currentTarget.value)}
                        />
                        <button
                          type="button"
                          aria-label={shown[item.key ?? ''] ? 'Hide' : 'Show'}
                          onclick={() =>
                            (shown = { ...shown, [item.key ?? '']: !shown[item.key ?? ''] })}
                          ><Icon
                            name={shown[item.key ?? ''] ? 'eye-slash' : 'eye'}
                            size={16}
                          /></button
                        >
                      </span>
                    {:else}
                      <input
                        id="admin-{item.key}"
                        class="input"
                        type={item.kind === 'number' ? 'number' : 'text'}
                        placeholder={item.placeholder}
                        value={text(item.key)}
                        oninput={(event) => set(item.key, event.currentTarget.value)}
                      />
                    {/if}
                  </div>
                  {#if item.note}<p class="note field-note">{item.note}</p>{/if}
                </div>
              {:else}
                <div class="block">
                  <div class="row" class:sub={item.sub} class:tall={item.kind === 'action'}>
                    <span class="row-label">
                      {item.label}
                      {#if item.experimental}<span class="experimental">Experimental</span>{/if}
                    </span>
                    {#if item.kind === 'switch'}
                      {#if item.locked}
                        <span class="locked" title={item.locked}>
                          <Switch on={false} label={item.label} onchange={() => {}} />
                        </span>
                      {:else}
                        <Switch
                          on={values[item.key ?? ''] === true}
                          label={item.label}
                          onchange={(next) => set(item.key, next)}
                        />
                      {/if}
                    {:else if item.kind === 'select'}
                      <SettingsSelect
                        label={item.label}
                        value={text(item.key)}
                        options={options(item).map(([value, label]) => ({ value, label }))}
                        onchange={(value) => set(item.key, value)}
                      />
                    {:else if item.kind === 'number'}
                      <span class="short">
                        <input
                          class="input number"
                          type="number"
                          aria-label={item.label}
                          value={text(item.key)}
                          oninput={(event) => set(item.key, Number(event.currentTarget.value))}
                        />
                        {#if item.unit}<span class="unit">{item.unit}</span>{/if}
                      </span>
                    {:else if item.kind === 'action'}
                      <button type="button" class="quiet" onclick={() => onaction?.(item.key ?? '')}
                        >{item.action}</button
                      >
                    {/if}
                  </div>
                  {#if item.note}<p class="note">{item.note}</p>{/if}
                  {#if item.locked}<p class="note">{item.locked}</p>{/if}
                </div>
              {/if}
            {/each}
          </div>
        </section>
      {/each}
    {/if}
  </div>
  <p class="sr-only" role="status">{notice}</p>
  {#if !panel.noSave}
    <div class="footer"><button type="submit" class="save">Save</button></div>
  {/if}
</form>

<style>
  /* Items fill the row; half items sit two to a row from 640 px (admin look G2). */
  .admin-panel .rows {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
  }

  /* A value or a field is a cell of the group, padded like a switch row. */
  .cell {
    padding: 12px 14px;
  }

  .admin-panel .rows > :global(* + *) {
    border-block-start: 1px solid var(--color-line-1);
  }

  .admin-panel .rows > :global(.half:first-child + .half) {
    border-block-start: 0;
  }

  @media (min-width: 40rem) {
    .admin-panel .rows {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .admin-panel .rows > :global(*) {
      grid-column: 1 / -1;
    }

    .admin-panel .rows > :global(.half) {
      grid-column: auto;
    }
  }

  .round {
    display: grid;
    place-items: center;
    inline-size: 24px;
    block-size: 24px;
    border-radius: 8px;
    color: var(--color-gray-400);
  }
  .round:hover {
    background-color: rgb(0 0 0 / 0.05);
    color: var(--color-gray-900);
  }
  .defaults-box {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-block-size: 448px;
    margin-block-start: 8px;
    padding: 0 4px 8px 0;
    overflow-y: auto;
  }
  .banner {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    margin-block-start: 8px;
  }
  .banner textarea {
    flex: 1;
  }
  .arena-form {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-block: 8px;
  }
  .check {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: var(--text-caption);
  }
  .arena-row {
    margin-block-start: 6px;
  }
  .workflow-actions {
    display: flex;
    gap: 8px;
  }
  .workflow-actions label {
    cursor: pointer;
  }
  .small {
    font-size: 11px;
  }

  .params-box {
    padding-block-start: 8px;
  }

  .info .label {
    line-height: 16px;
  }

  .info .label.muted {
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) .info .label.muted {
    color: var(--color-gray-600);
  }

  .admin-panel .info-note {
    margin-block-start: 6px;
  }

  /* As the running app measures: the parameters row is 20 px tall, and an inline text area
     leaves a line's descender space under it. */
  .params-row {
    min-block-size: 20px;
  }

  .area {
    margin-block-end: 5px;
  }

  .admin-panel section + section {
    margin-block-start: 20px;
  }

  .heading {
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) .heading {
    color: var(--color-gray-600);
  }

  .info {
    display: flex;
    flex-direction: column;
    font-size: var(--text-caption);
  }

  .label,
  .field-label {
    color: var(--color-gray-600);
    font-size: var(--text-caption);
    line-height: 20px;
  }

  .value {
    color: var(--color-gray-700);
  }

  :global([data-theme='dark']) :is(.label, .field-label) {
    color: var(--color-gray-400);
  }

  :global([data-theme='dark']) .value {
    color: var(--color-gray-200);
  }

  .field-control {
    margin-block-start: 3px;
  }

  .admin-panel .field-note {
    margin-block-start: 2px;
  }

  /* Action rows are 20 px tall with the action 1 px below centre, as on Data Controls. */
  .row.tall .quiet {
    padding-block-start: 2px;
  }

  .row.sub .row-label {
    color: var(--color-gray-500);
  }

  .row-label {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    min-inline-size: 0;
  }

  .experimental {
    color: var(--color-gray-400);
    font-size: 10px;
    line-height: 1;
    text-transform: uppercase;
  }

  :global([data-theme='dark']) .experimental {
    color: var(--color-gray-600);
  }

  .input,
  .secret {
    inline-size: 100%;
    block-size: 28px;
    padding-inline: 8px;
    border: 1px solid color-mix(in srgb, var(--color-gray-100) 50%, transparent);
    border-radius: 8px;
    background-color: color-mix(in srgb, var(--color-gray-50) 40%, transparent);
    color: var(--color-gray-700);
    font-size: var(--text-caption);
    transition: border-color 150ms;
  }

  .input::placeholder,
  .secret input::placeholder {
    color: var(--color-gray-300);
  }

  .input:focus,
  .secret:focus-within {
    border-color: var(--color-blue-400);
    outline: none;
  }

  :global([data-theme='dark']) :is(.input, .secret) {
    border-color: rgb(255 255 255 / 0.04);
    background-color: rgb(255 255 255 / 0.03);
    color: var(--color-gray-300);
  }

  :global([data-theme='dark']) :is(.input, .secret input)::placeholder {
    color: var(--color-gray-700);
  }

  .secret {
    display: flex;
    align-items: center;
  }

  .secret input {
    flex: 1;
    background: transparent;
    color: inherit;
    font-size: var(--text-caption);
  }

  .secret input:focus {
    outline: none;
  }

  .secret button {
    display: grid;
    margin-inline-start: 6px;
    color: var(--color-gray-400);
  }

  .area {
    field-sizing: content;
    min-block-size: 28px;
  }

  .short {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .number {
    inline-size: 64px;
    text-align: end;
    appearance: textfield;
  }

  .unit {
    color: var(--color-gray-500);
    font-size: var(--text-caption);
  }

  .locked {
    cursor: not-allowed;
    opacity: 0.75;
    pointer-events: none;
  }
</style>
