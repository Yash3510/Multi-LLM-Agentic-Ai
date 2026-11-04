<script module lang="ts">
  import type { SectionMeta } from '../section';

  // English until the ui_section_fields and ui_fields_* messages exist (requested); the captions
  // below are the same. Demo data is sector-neutral: rule R2, parameter Ratio, ids like CASE-0142.
  export const section: SectionMeta = {
    id: 'fields',
    title: () => 'Fields',
    description: () =>
      'Field, text input, textarea, select, combobox, checkbox, radio group and segmented control, in every state, density and both languages.',
  };
</script>

<script lang="ts">
  import Checkbox from '$lib/ui/components/Checkbox.svelte';
  import Combobox from '$lib/ui/components/Combobox.svelte';
  import Field from '$lib/ui/components/Field.svelte';
  import OnOffChoice from '$lib/ui/components/OnOffChoice.svelte';
  import RadioGroup from '$lib/ui/components/RadioGroup.svelte';
  import SegmentedControl from '$lib/ui/components/SegmentedControl.svelte';
  import Select from '$lib/ui/components/Select.svelte';
  import Textarea from '$lib/ui/components/Textarea.svelte';
  import TextInput from '$lib/ui/components/TextInput.svelte';
  import { formatHashShort, formatPercent, formatQuantity } from '$lib/ui/format';

  type State =
    | 'empty'
    | 'default'
    | 'hover'
    | 'focus'
    | 'active'
    | 'chosen'
    | 'mixed'
    | 'invalid'
    | 'disabled'
    | 'disabledChosen'
    | 'readonly';
  type Preview = 'hover' | 'focus' | 'active';

  const PREVIEWED: State[] = ['hover', 'focus', 'active'];
  const preview = (state: State) => (PREVIEWED.includes(state) ? (state as Preview) : undefined);

  // Rows of the text-field matrix; hover, focus and active are drawn still with data-preview.
  const TEXT_STATES: { state: State; caption: string }[] = [
    { state: 'empty', caption: 'empty' },
    { state: 'default', caption: 'filled' },
    { state: 'hover', caption: 'hover' },
    { state: 'focus', caption: 'focus-visible' },
    { state: 'active', caption: 'active' },
    { state: 'invalid', caption: 'invalid' },
    { state: 'disabled', caption: 'disabled' },
    { state: 'readonly', caption: 'read-only' },
  ];
  const TEXT_COLUMNS = [
    { kind: 'input', name: 'TextInput', note: 'Single line; inset radius' },
    { kind: 'textarea', name: 'Textarea', note: 'Grows with its text' },
    { kind: 'select', name: 'Select', note: 'A short list; the trigger presses' },
    { kind: 'combobox', name: 'Combobox', note: 'Type to narrow a longer list' },
  ] as const;

  const CHOICE_STATES: { state: State; caption: string }[] = [
    { state: 'empty', caption: 'unchosen' },
    { state: 'hover', caption: 'hover' },
    { state: 'focus', caption: 'focus-visible' },
    { state: 'active', caption: 'active' },
    { state: 'chosen', caption: 'chosen' },
    { state: 'mixed', caption: 'mixed' },
    { state: 'invalid', caption: 'invalid' },
    { state: 'disabled', caption: 'disabled' },
    { state: 'disabledChosen', caption: 'disabled, chosen' },
    { state: 'readonly', caption: 'read-only, chosen' },
  ];
  const CHOICE_COLUMNS = [
    { kind: 'checkbox', name: 'Checkbox', note: 'On or off in lists and forms; ink when ticked' },
    { kind: 'radio', name: 'RadioGroup', note: 'One of a few, all visible; ink dot' },
    { kind: 'segments', name: 'SegmentedControl', note: 'One of two to five short options' },
  ] as const;
  type TextKind = (typeof TEXT_COLUMNS)[number]['kind'];
  type ChoiceKind = (typeof CHOICE_COLUMNS)[number]['kind'];

  // Fields that take text have no pressed look; only the Select trigger is pressed.
  const typingPreview = (state: State) =>
    state === 'hover' || state === 'focus' ? state : undefined;
  const NAMES: Record<TextKind, string> = {
    input: 'Ratio',
    textarea: 'Note',
    select: 'Unit',
    combobox: 'Rule',
  };
  // Each message says what to do, not only what is wrong.
  const ERRORS: Record<TextKind | ChoiceKind, string> = {
    input: 'Enter a value between 0 and 1',
    textarea: 'Add a note before sending',
    select: 'Choose a unit',
    combobox: 'Choose a rule from the list',
    checkbox: 'Tick R2 to run it',
    radio: 'Choose a unit',
    segments: 'Choose a unit',
  };

  const UNITS = [
    { value: 's', label: 'Seconds (s)' },
    { value: 'pct', label: 'Percent (%)' },
    { value: 'inr', label: 'Rupees (₹)' },
    { value: 'min', label: 'Minutes', disabled: true },
  ];
  const UNITS_HI = [
    { value: 's', label: 'सेकंड (s)' },
    { value: 'pct', label: 'प्रतिशत (%)' },
    { value: 'inr', label: 'रुपये (₹)' },
  ];
  const UNIT_CHOICES = [
    {
      value: 's',
      label: 'Seconds',
      description: `Durations under ${formatQuantity(10, 's')} keep one decimal: ${formatQuantity(3.7, 's')}`,
    },
    {
      value: 'pct',
      label: 'Percent',
      description: `Ratio shown as a share: ${formatPercent(0.42)}`,
    },
    {
      value: 'inr',
      label: 'Rupees',
      description: 'Not used by R2',
      disabled: true,
    },
  ];
  const PAIR = [
    { value: 's', label: 'Seconds' },
    { value: 'pct', label: 'Percent' },
  ];
  const RANGES = [
    { value: 'today', label: 'Today' },
    { value: '7d', label: '7 days' },
    { value: '30d', label: '30 days' },
  ];
  const RANGES_HI = [
    { value: 'today', label: 'आज' },
    { value: '7d', label: '7 दिन' },
    { value: '30d', label: '30 दिन' },
  ];
  const RULES = [
    'Ratio within limit',
    'Ratio above limit',
    `Duration under ${formatQuantity(10, 's')}`,
    'Count per case',
    'Share of total (%)',
    'Amount in ₹',
    'Interval between entries',
    'Score from the Reader',
    'Rate per minute',
    'Gap between cases',
    'Total across cases',
    'Spread of values',
  ].map((name, index) => ({
    value: `R${index + 1}`,
    label: `R${index + 1} · ${name}`,
    disabled: index === 11,
  }));
  const RULES_HI = [
    'अनुपात सीमा में',
    'अनुपात सीमा से ऊपर',
    `अवधि ${formatQuantity(10, 's')} से कम`,
    'प्रति मामला गिनती',
  ].map((name, index) => ({ value: `R${index + 1}`, label: `R${index + 1} · ${name}` }));
  const DENSITIES = [
    { density: 'comfortable', caption: 'comfortable: 40 px' },
    { density: 'default', caption: 'default: 32 px' },
    { density: 'compact', caption: 'compact: 28 px, small type' },
  ];
  // A receipt fingerprint: shown as 8 characters, copied whole.
  const HASH = '9f2c1a7be04d63c8a51f27e9d0b4c6a3e8f1d2b7c9a05e6f4b3d2c1a0f9e8d7c';
  const NOTE =
    'Ratio for CASE-0142 is 0.42, inside the R2 limit.\nChecked against 3 files; 1 set aside as unreadable.';

  // Interactive demos. The Ratio field checks as you type, so the error row can be watched opening.
  let ratio = $state('0.42');
  const ratioError = $derived.by(() => {
    if (!ratio.trim()) return 'Enter a value for Ratio';
    const number = Number(ratio);
    return Number.isFinite(number) && number >= 0 && number <= 1
      ? undefined
      : 'Enter a value between 0 and 1';
  });
  let search = $state('CASE-0142');
  let note = $state(NOTE);
  let unit = $state('pct');
  let unitHi = $state('s');
  let rule = $state('R2');
  let ruleHi = $state('');
  let pick = $state('s');
  let pickHi = $state('pct');
  let range = $state('7d');
  let rangeHi = $state('today');
  let unitsShown = $state(true);
  let railShown = $state(false);

  // A checkbox list with a "select all" that is mixed while some, not all, are ticked.
  let rules = $state([
    { id: 'R1', label: 'R1 · Ratio within limit', on: true },
    { id: 'R2', label: 'R2 · Ratio above limit', on: false },
    { id: 'R3', label: `R3 · Duration under ${formatQuantity(10, 's')}`, on: false },
  ]);
  const allOn = $derived(rules.every((item) => item.on));
  const someOn = $derived(rules.some((item) => item.on));
  const rulesError = $derived(someOn ? undefined : 'Pick at least one rule to run');

  function setAll(on: boolean) {
    for (const item of rules) item.on = on;
  }
</script>

{#snippet na()}
  <span class="text-ink-3" aria-hidden="true">—</span>
  <span class="sr-only">Does not apply</span>
{/snippet}

<!-- One text-like field in one state. Each is named for its column and row, as a label would. -->
{#snippet textCell(kind: TextKind, state: State, caption: string)}
  {@const filled = state !== 'empty'}
  {@const props = {
    'aria-label': `${NAMES[kind]}, ${caption}`,
    invalid: state === 'invalid',
    disabled: state === 'disabled',
    readonly: state === 'readonly',
  }}
  {#if kind === 'input'}
    <TextInput
      {...props}
      value={filled ? '0.42' : ''}
      placeholder="0 to 1"
      clearable
      preview={typingPreview(state)}
    />
  {:else if kind === 'textarea'}
    <Textarea
      {...props}
      value={filled ? 'Ratio for CASE-0142 is 0.42.' : ''}
      placeholder="Add a note"
      rows={2}
      preview={typingPreview(state)}
    />
  {:else if kind === 'select'}
    <Select
      {...props}
      options={UNITS}
      value={filled ? 'pct' : ''}
      placeholder="Choose a unit"
      preview={preview(state)}
    />
  {:else}
    <Combobox
      {...props}
      options={RULES}
      value={filled ? 'R2' : ''}
      placeholder="Find a rule"
      preview={typingPreview(state)}
    />
  {/if}
{/snippet}

<!-- One choice control in one state. -->
{#snippet choiceCell(kind: ChoiceKind, state: State, caption: string)}
  {@const chosen = ['chosen', 'disabledChosen', 'readonly'].includes(state)}
  {@const props = {
    invalid: state === 'invalid',
    disabled: state === 'disabled' || state === 'disabledChosen',
    readonly: state === 'readonly',
    preview: preview(state),
  }}
  {#if kind === 'checkbox'}
    <Checkbox {...props} label="R2 · Ratio" checked={chosen} indeterminate={state === 'mixed'} />
  {:else if state === 'mixed'}
    {@render na()}
  {:else if kind === 'radio'}
    <RadioGroup {...props} aria-label="Unit, {caption}" options={PAIR} value={chosen ? 's' : ''} />
  {:else}
    <!-- The preview lands on the first segment, so the second carries the choice there. -->
    <SegmentedControl
      {...props}
      aria-label="Unit, {caption}"
      options={PAIR}
      value={chosen ? 's' : preview(state) ? 'pct' : ''}
    />
  {/if}
{/snippet}

<!-- Rows are states and columns components. On a tablet the table scrolls sideways, never the page. -->
{#snippet matrix(kind: 'text' | 'choice')}
  {@const columns = kind === 'text' ? TEXT_COLUMNS : CHOICE_COLUMNS}
  {@const states = kind === 'text' ? TEXT_STATES : CHOICE_STATES}
  <div class="scroller">
    <table class="matrix" data-kind={kind}>
      <thead>
        <tr>
          <th scope="col"><span class="sr-only">State</span></th>
          {#each columns as column (column.kind)}
            <th scope="col">
              <span class="block text-small font-medium text-ink-1">{column.name}</span>
              <span class="block text-caption font-normal text-ink-3">{column.note}</span>
            </th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each states as { state, caption } (state)}
          <tr>
            <th scope="row" class="font-mono text-caption font-normal text-ink-3">{caption}</th>
            {#if kind === 'text'}
              {#each TEXT_COLUMNS as column (column.kind)}
                <td>
                  {#if state === 'active' && column.kind !== 'select'}
                    {@render na()}
                  {:else if state === 'invalid'}
                    <Field error={ERRORS[column.kind]}>
                      {@render textCell(column.kind, state, caption)}
                    </Field>
                  {:else}
                    {@render textCell(column.kind, state, caption)}
                  {/if}
                </td>
              {/each}
            {:else}
              {#each CHOICE_COLUMNS as column (column.kind)}
                <td>
                  {#if state === 'invalid'}
                    <Field error={ERRORS[column.kind]} group={column.kind !== 'checkbox'}>
                      {@render choiceCell(column.kind, state, caption)}
                    </Field>
                  {:else}
                    {@render choiceCell(column.kind, state, caption)}
                  {/if}
                </td>
              {/each}
            {/if}
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/snippet}

<!-- English in every locale until the messages exist, so it says so; the Hindi rows set their own. -->
<div class="flex flex-col gap-10" lang="en">
  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Text fields: every state</h3>
    {@render matrix('text')}
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Choices: every state</h3>
    {@render matrix('choice')}
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Field</h3>
    <dl class="rows">
      <div class="row">
        <dt>
          Label, description and the word Required. The error opens below with its icon, growing
          from 0fr to 1fr; type a value outside 0 to 1 to watch it
        </dt>
        <dd>
          <Field
            class="slot"
            label="Ratio"
            description="Share of the R2 limit used by CASE-0142"
            error={ratioError}
            required
          >
            <TextInput bind:value={ratio} inputmode="decimal" placeholder="0 to 1" clearable />
          </Field>
        </dd>
      </div>
      <div class="row">
        <dt>
          A group: the label names the set. "All rules" is mixed while some, not all, are ticked;
          untick every rule to see the group's error
        </dt>
        <dd>
          <Field
            class="slot"
            label="Rules to run"
            description="Each one runs on CASE-0142"
            error={rulesError}
            required
            group
          >
            <Checkbox
              label="All rules"
              checked={allOn}
              indeterminate={someOn && !allOn}
              onCheckedChange={setAll}
            />
            <div class="nested">
              {#each rules as item (item.id)}
                <Checkbox label={item.label} bind:checked={item.on} />
              {/each}
            </div>
          </Field>
        </dd>
      </div>
      <div class="row">
        <dt>
          Disabled: ink-disabled text and a line-1 border. The description stays readable, to say
          why
        </dt>
        <dd>
          <Field class="slot" label="Ratio" description="Locked while R2 runs" disabled>
            <TextInput value="0.42" />
          </Field>
          <Field class="slot" label="Unit" description="Set by the rule pack" disabled>
            <Select options={UNITS} value="pct" />
          </Field>
        </dd>
      </div>
      <div class="row">
        <dt>
          Read-only: sunken fill and a copy button with its hint. A sealed record leads with the
          lock
        </dt>
        <dd>
          <Field class="slot" label="Case" readonly>
            <TextInput value="CASE-0142" class="font-mono" />
          </Field>
          <Field class="slot" label="Receipt fingerprint" description="Sealed when released">
            <TextInput value={formatHashShort(HASH)} copyValue={HASH} sealed class="font-mono" />
          </Field>
          <Field class="slot" label="Unit" readonly>
            <Select options={UNITS} value="s" />
          </Field>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">TextInput and Textarea</h3>
    <dl class="rows">
      <div class="row">
        <dt>
          A leading or trailing icon says what the field takes. The clear button appears with text;
          its hint opens on hover and on focus
        </dt>
        <dd>
          <span class="slot">
            <TextInput
              type="search"
              bind:value={search}
              prefix="magnifying-glass"
              placeholder="Search cases"
              aria-label="Search cases"
              clearable
            />
          </span>
          <span class="slot">
            <TextInput
              prefix="fingerprint"
              placeholder="First 8 characters"
              aria-label="Fingerprint prefix"
              class="font-mono"
            />
          </span>
          <span class="slot">
            <TextInput value="0.42" suffix="calculation" aria-label="Ratio, worked out" />
          </span>
        </dd>
      </div>
      <div class="row">
        <dt>
          Textarea grows with its text from 2 lines to 6, then scrolls. Type or paste to watch it;
          nothing jumps
        </dt>
        <dd>
          <Field class="slot" label="Note" description="Kept with CASE-0142">
            <Textarea bind:value={note} rows={2} maxRows={6} />
          </Field>
          <Field class="slot" label="Note" readonly>
            <Textarea value={NOTE} rows={2} />
          </Field>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Select and Combobox</h3>
    <dl class="rows">
      <div class="row">
        <dt>
          Select: a short list. Arrow keys, Home and End, and type-ahead on the closed trigger; the
          chosen option is the selected recipe plus a tick. A disabled option stays in view
        </dt>
        <dd>
          <Field class="slot" label="Unit" description="Shown beside every value" required>
            <Select options={UNITS} bind:value={unit} placeholder="Choose a unit" />
          </Field>
        </dd>
      </div>
      <div class="row">
        <dt>
          Combobox: type to narrow a longer list. Label starts rank first and the count is spoken;
          Escape or leaving puts the chosen label back
        </dt>
        <dd>
          <Field class="slot" label="Rule" description="12 rules in the pack">
            <Combobox
              options={RULES}
              bind:value={rule}
              prefix="magnifying-glass"
              placeholder="Find a rule"
            />
          </Field>
          <Field class="slot" label="Rule" description="Open it: the list is still arriving">
            <Combobox options={[]} loading placeholder="Find a rule" />
          </Field>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Checkbox and RadioGroup</h3>
    <dl class="rows">
      <div class="row">
        <dt>
          Checkboxes in lists and forms; ticked is ink, a person's choice, never violet. A press
          anywhere on the row toggles
        </dt>
        <dd>
          <Checkbox label="Show units beside values" checked />
          <Checkbox
            label="Keep CASE-0142 open after sign-off"
            description="It stays in the side panel until closed"
          />
        </dd>
      </div>
      <div class="row">
        <dt>
          RadioGroup: one of a few, all visible. One tab stop; arrow keys move and choose. A
          disabled option says why
        </dt>
        <dd>
          <Field class="slot" label="Unit for Ratio" required group>
            <RadioGroup options={UNIT_CHOICES} bind:value={pick} />
          </Field>
        </dd>
      </div>
      <div class="row">
        <dt>Side by side for two or three short options</dt>
        <dd>
          <Field label="Unit" group>
            <RadioGroup options={PAIR} bind:value={pick} orientation="horizontal" />
          </Field>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">SegmentedControl and the on/off choice</h3>
    <dl class="rows">
      <div class="row">
        <dt>
          One of two to five short options in one strip. The chosen segment: accent-soft fill, a 2
          px accent edge, ink-1 text
        </dt>
        <dd>
          <Field label="Range" group>
            <SegmentedControl options={RANGES} bind:value={range} />
          </Field>
          <Field class="slot" label="Range" description="Sharing the width" group>
            <SegmentedControl options={RANGES} bind:value={range} fill />
          </Field>
        </dd>
      </div>
      <div class="row">
        <dt>
          On or off is a worded choice, never a sliding switch. Name the states for what they do
          where plain Off and On would be vague
        </dt>
        <dd>
          <Field label="Units beside values" group>
            <OnOffChoice bind:checked={unitsShown} offLabel="Hidden" onLabel="Shown" />
          </Field>
          <Field label="Stage rail in the thread" group>
            <OnOffChoice bind:checked={railShown} />
          </Field>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Density, reduced motion and Hindi</h3>
    <dl class="rows">
      <div class="row">
        <dt>Heights follow the region's density; compact also drops to the small type step</dt>
        <dd class="densities">
          {#each DENSITIES as { density, caption } (density)}
            <div class="flex flex-col gap-2" data-density={density}>
              <Field label="Ratio">
                <TextInput value="0.42" clearable />
              </Field>
              <Select aria-label="Unit, {density}" options={UNITS} value="pct" />
              <Checkbox label="R2 · Ratio" checked />
              <SegmentedControl aria-label="Range, {density}" options={RANGES} value="7d" />
              <span class="text-caption text-ink-3">{caption}</span>
            </div>
          {/each}
        </dd>
      </div>
      <div class="row">
        <dt>
          Reduced motion: the error row appears without growing, a crossfade of 120 ms at most. It
          shares its value with the Ratio field above
        </dt>
        <dd data-motion="reduce">
          <Field class="slot" label="Ratio" error={ratioError} required>
            <TextInput bind:value={ratio} inputmode="decimal" clearable />
          </Field>
        </dd>
      </div>
      <div class="row">
        <dt>
          Hindi: 0.15 more line height so matras are never clipped, no capitals, the same widths
        </dt>
        <dd lang="hi" class="hindi">
          <Field
            class="slot"
            label="अनुपात"
            description="CASE-0142 के लिए R2 सीमा का हिस्सा"
            error={ratioError && '0 और 1 के बीच का मान दर्ज करें'}
            requiredLabel="आवश्यक"
            required
          >
            <TextInput bind:value={ratio} inputmode="decimal" clearable clearLabel="साफ़ करें" />
          </Field>
          <Field class="slot" label="इकाई" description="हर मान के साथ दिखाई जाती है">
            <Select options={UNITS_HI} bind:value={unitHi} placeholder="इकाई चुनें" />
          </Field>
          <Field class="slot" label="नियम">
            <Combobox
              options={RULES_HI}
              bind:value={ruleHi}
              placeholder="नियम खोजें"
              clearLabel="साफ़ करें"
              showOptionsLabel="विकल्प दिखाएँ"
              noMatchesText="कोई मेल नहीं"
            />
          </Field>
          <Field class="slot" label="टिप्पणी" readonly>
            <Textarea
              rows={2}
              value="CASE-0142 का अनुपात 0.42 है, R2 सीमा के भीतर।"
              copyLabel="कॉपी करें"
              copiedLabel="कॉपी हो गया"
            />
          </Field>
          <Field label="इकाई चुनें" group>
            <RadioGroup options={UNITS_HI} bind:value={pickHi} />
          </Field>
          <div class="flex flex-col items-start gap-3">
            <Checkbox label="सभी नियम" indeterminate />
            <Field label="अवधि" group>
              <SegmentedControl options={RANGES_HI} bind:value={rangeHi} />
            </Field>
            <Field label="मानों के साथ इकाइयाँ" group>
              <OnOffChoice bind:checked={unitsShown} offLabel="छिपी" onLabel="दिखाई गई" />
            </Field>
          </div>
        </dd>
      </div>
    </dl>
  </div>
</div>

<style>
  /* Caption on the left, examples on the right; stacked when narrow. */
  .rows {
    display: flex;
    flex-direction: column;
  }

  .row {
    display: grid;
    gap: var(--spacing-2) var(--spacing-6);
    padding-block: var(--spacing-3);
    border-top: 1px solid var(--color-line-1);
  }

  @media (min-width: 48rem) {
    .row {
      grid-template-columns: 14rem minmax(0, 1fr);
      align-items: start;
    }
  }

  dt {
    font-size: var(--text-caption);
    line-height: var(--text-caption--line-height);
    color: var(--color-ink-3);
  }

  dd {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-start;
    gap: var(--spacing-4) var(--spacing-6);
    min-width: 0;
  }

  /* A field's width in the examples: six 48 px steps, never wider than the room. */
  dd :global(.slot) {
    width: min(100%, calc(var(--spacing-12) * 6));
  }

  .nested {
    display: flex;
    flex-direction: column;
    padding-inline-start: var(--spacing-6);
  }

  .densities > div {
    width: min(100%, calc(var(--spacing-12) * 4.5));
  }

  .hindi {
    row-gap: var(--spacing-6);
  }

  /* Only the table scrolls sideways, never the page. */
  .scroller {
    overflow-x: auto;
  }

  /* Fixed columns share the width, so every state of one component lines up; below the minimum
     the table scrolls sideways instead of squeezing the fields. */
  .matrix {
    width: 100%;
    min-width: calc(var(--spacing-12) * 18);
    border-collapse: collapse;
    table-layout: fixed;
    text-align: start;
  }

  .matrix thead th:first-child {
    width: calc(var(--spacing-12) * 3);
  }

  .matrix th,
  .matrix td {
    padding: var(--spacing-2) var(--spacing-3);
    border-top: 1px solid var(--color-line-1);
    text-align: start;
    vertical-align: top;
  }

  .matrix thead th {
    border-top: 0;
    vertical-align: bottom;
  }

  .matrix tbody th {
    padding-block-start: var(--spacing-3);
    white-space: nowrap;
  }
</style>
