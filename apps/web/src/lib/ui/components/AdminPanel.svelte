<script lang="ts">
  // One admin settings panel drawn from its schema (admin look §19, P1 to P4): sections of rows
  // and fields with switches, selects, inputs, text areas, secret fields and text actions. Values
  // start from the schema's defaults overlaid with the stored ones; Save stores them all.
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
    notice = 'Settings saved successfully!';
  }
</script>

<form class="settings-page admin-panel" onsubmit={save}>
  <div class="body">
    <h2>{panel.title}</h2>
    {#if values}
      {#each panel.sections as section, index (index)}
        <section>
          {#if section.heading}<h3 class="heading">{section.heading}</h3>{/if}
          <div class="rows">
            {#each shownItems(section, values) as item (item.key ?? item.label)}
              {#if item.kind === 'info'}
                <div class="info">
                  <span class="label">{item.label}</span>
                  {#if item.value}<span class="value">{item.value}</span>{/if}
                  {#if item.note}<p class="note info-note">{item.note}</p>{/if}
                </div>
              {:else if item.kind === 'params'}
                <div>
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
                <div class:half={item.half}>
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
    column-gap: 12px;
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

  .small {
    font-size: 11px;
  }

  .params-box {
    padding-block-start: 8px;
  }

  .info .label {
    line-height: 16px;
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
