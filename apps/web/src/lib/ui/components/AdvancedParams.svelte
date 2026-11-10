<script lang="ts">
  // The advanced parameters list (chat-composer look §10, F74): each parameter's name and its
  // state button; Custom shows a slider with a number box, or a text field.
  import { next, setValue, shownParams, stateLabel, type ParamValue } from '$lib/ui/params';

  type Props = {
    params: Record<string, ParamValue>;
    admin?: boolean;
    /** One column, or the 1/2/3-column grid the model editor uses. */
    grid?: boolean;
  };

  let { params = $bindable(), admin = false, grid = false }: Props = $props();

  function set(key: string, value: ParamValue | undefined) {
    const copy = { ...params };
    if (value === undefined) delete copy[key];
    else copy[key] = value;
    params = copy;
  }
</script>

<div class="list" class:grid>
  {#each shownParams(admin) as param (param.key)}
    {@const value = params[param.key]}
    <div class="param" data-param={param.key}>
      <div class="head">
        <span title={param.help}>{param.label}</span>
        <button type="button" class="state" onclick={() => set(param.key, next(param, value))}
          ><span>{stateLabel(param, value)}</span></button
        >
      </div>
      {#if value !== undefined && param.kind === 'number' && param.min !== undefined}
        <div class="custom">
          <input
            type="range"
            min={param.min}
            max={param.max}
            step={param.step}
            value={Number(value)}
            aria-label={param.label}
            oninput={(event) => set(param.key, setValue(param, event.currentTarget.value) ?? value)}
          />
          <input
            class="number"
            type="number"
            min={param.min}
            max={param.max}
            step={param.step}
            value={Number(value)}
            aria-label={`${param.label} value`}
            onchange={(event) =>
              set(param.key, setValue(param, event.currentTarget.value) ?? value)}
          />
        </div>
      {:else if value !== undefined && (param.kind === 'text' || param.kind === 'number')}
        <div class="custom">
          <input
            class="text"
            value={String(value)}
            placeholder={param.placeholder}
            aria-label={param.label}
            oninput={(event) => set(param.key, setValue(param, event.currentTarget.value) ?? value)}
          />
        </div>
      {/if}
    </div>
  {/each}
</div>

<style>
  .list {
    display: flex;
    flex-direction: column;
    color: var(--color-gray-600);
    font-size: var(--text-caption);
  }

  .list.grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 4px 20px;
  }

  @media (min-width: 40rem) {
    .list.grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (min-width: 64rem) {
    .list.grid {
      grid-template-columns: repeat(3, 1fr);
    }
  }

  :global([data-theme='dark']) .list {
    color: var(--color-gray-400);
  }

  .param {
    inline-size: 100%;
    padding-block: 2px;
  }

  .head {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .state {
    flex-shrink: 0;
    padding: 4px 12px;
    border-radius: 4px;
    font-size: var(--text-caption);
    transition: background-color 150ms;
  }

  .state span {
    margin-inline-start: 8px;
  }

  .state:focus-visible {
    outline: 2px solid var(--color-blue-500);
    outline-offset: -2px;
  }

  .custom {
    display: flex;
    gap: 8px;
    margin-block-start: 2px;
  }

  input[type='range'] {
    flex: 1;
    block-size: 8px;
    margin-block: auto;
    border-radius: 8px;
    cursor: pointer;
    accent-color: var(--color-gray-700);
  }

  .number {
    inline-size: 56px;
    background: transparent;
    color: inherit;
    text-align: center;
  }

  .text {
    inline-size: 100%;
    background: transparent;
    color: inherit;
    font-size: var(--text-ui);
  }

  :is(.number, .text):focus {
    outline: none;
  }
</style>
