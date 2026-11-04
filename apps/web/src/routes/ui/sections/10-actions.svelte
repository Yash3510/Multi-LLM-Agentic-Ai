<script module lang="ts">
  import type { SectionMeta } from '../section';

  // English until the ui_section_actions and ui_actions_* messages exist (requested); the captions
  // below are the same. Demo data is sector-neutral: rule R2, parameter Ratio, ids like CASE-0142.
  export const section: SectionMeta = {
    id: 'actions',
    title: () => 'Actions',
    description: () =>
      'Buttons, icon buttons, text buttons, links, key caps and button groups, in every state, density and both languages.',
  };
</script>

<script lang="ts">
  import { untrack } from 'svelte';
  import type { ActionVariant } from '$lib/ui/components/ActionBase.svelte';
  import Button from '$lib/ui/components/Button.svelte';
  import ButtonGroup from '$lib/ui/components/ButtonGroup.svelte';
  import IconButton from '$lib/ui/components/IconButton.svelte';
  import Kbd from '$lib/ui/components/Kbd.svelte';
  import Link from '$lib/ui/components/Link.svelte';
  import TextButton from '$lib/ui/components/TextButton.svelte';
  import type { IconName } from '$lib/ui/icons/generated/icons';
  import ReplayButton from '../ReplayButton.svelte';
  import { replay } from '../replay.svelte';

  type State = 'default' | 'hover' | 'focus' | 'active' | 'selected' | 'disabled' | 'loading';
  type IconVariant = Exclude<ActionVariant, 'decision'>;

  // The rows of each matrix. hover, focus and active are drawn still with data-preview.
  const STATES: { state: State; caption: string }[] = [
    { state: 'default', caption: 'default' },
    { state: 'hover', caption: 'hover' },
    { state: 'focus', caption: 'focus-visible' },
    { state: 'active', caption: 'active' },
    { state: 'selected', caption: 'selected' },
    { state: 'disabled', caption: 'disabled' },
    { state: 'loading', caption: 'loading' },
  ];
  const PREVIEWED: State[] = ['hover', 'focus', 'active'];
  // Only a toolbar control whose panel is open is ever "on"; a decision or a primary never is.
  const SELECTABLE: ActionVariant[] = ['secondary', 'quiet'];
  const REASON = 'Waiting for R2 to finish';

  const BUTTONS: { variant: ActionVariant; label: string; note: string }[] = [
    {
      variant: 'decision',
      label: 'Apply changes',
      note: 'Decision: solid ink, only to confirm, allow, approve, sign or apply. Never violet',
    },
    { variant: 'primary', label: 'Run R2', note: 'Primary: the everyday main action, raised' },
    { variant: 'secondary', label: 'Save draft', note: 'Secondary: the default' },
    { variant: 'quiet', label: 'Show all rules', note: 'Quiet: low emphasis, toolbars' },
    { variant: 'danger', label: 'Discard draft', note: 'Danger: destructive, in stop ink' },
  ];
  const ICONS: { variant: IconVariant; icon: IconName; label: string }[] = [
    { variant: 'primary', icon: 'arrow-clockwise', label: 'Re-run R2' },
    { variant: 'secondary', icon: 'download-simple', label: 'Download receipt' },
    { variant: 'quiet', icon: 'copy', label: 'Copy case id' },
    { variant: 'danger', icon: 'x', label: 'Remove file' },
  ];
  const DENSITIES = [
    { density: 'comfortable', caption: '40 px · small 36' },
    { density: 'default', caption: '32 px · small 28' },
    { density: 'compact', caption: '28 px · small 24' },
  ];
  const SEARCH = ['mod', 'k'];
  const RUN = ['mod', 'enter'];
  const SAVE = ['mod', 's'];

  // Interactive demos: each press loads for a set time, as a real request would.
  let exporting = $state(false);
  let saving = $state(false);
  let refreshing = $state(false);
  let filters = $state(true);
  let panel = $state(false);
  let ringRun = $state(0);

  function load(set: (value: boolean) => void, ms: number) {
    set(true);
    setTimeout(() => set(false), ms);
  }

  // The toolbar's Replay remounts the width-lock demo, so its ring arrives again after 300 ms.
  $effect(() => {
    if (replay.count > 0) untrack(() => (ringRun += 1));
  });
</script>

{#snippet na()}
  <span class="text-ink-3" aria-hidden="true">—</span>
  <span class="sr-only">Does not apply</span>
{/snippet}

<!-- Rows are states and columns variants. On a tablet the table scrolls sideways, never the page. -->
{#snippet matrix(kind: 'button' | 'icon')}
  {@const columns = kind === 'button' ? BUTTONS : ICONS}
  <div class="scroller">
    <table class="matrix">
      <thead>
        <tr>
          <th scope="col"><span class="sr-only">State</span></th>
          {#each columns as column (column.variant)}
            <th scope="col">
              <span class="block text-small font-medium text-ink-1">{column.variant}</span>
              {#if 'note' in column}
                <span class="block text-caption font-normal text-ink-3">{column.note}</span>
              {/if}
            </th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each STATES as { state, caption } (state)}
          {@const preview = PREVIEWED.includes(state) ? state : undefined}
          <tr>
            <th scope="row" class="font-mono text-caption font-normal text-ink-3">{caption}</th>
            {#if kind === 'button'}
              {#each BUTTONS as { variant, label } (variant)}
                <td>
                  {#if state === 'selected' && !SELECTABLE.includes(variant)}
                    {@render na()}
                  {:else}
                    <Button
                      {variant}
                      data-preview={preview}
                      pressed={state === 'selected' || undefined}
                      disabled={state === 'disabled'}
                      reason={state === 'disabled' ? REASON : undefined}
                      loading={state === 'loading'}
                    >
                      {label}
                    </Button>
                  {/if}
                </td>
              {/each}
            {:else}
              {#each ICONS as { variant, icon, label } (variant)}
                <td>
                  {#if state === 'selected' && !SELECTABLE.includes(variant)}
                    {@render na()}
                  {:else}
                    <IconButton
                      {icon}
                      {label}
                      {variant}
                      data-preview={preview}
                      pressed={state === 'selected' || undefined}
                      disabled={state === 'disabled'}
                      reason={state === 'disabled' ? REASON : undefined}
                      loading={state === 'loading'}
                    />
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
    <h3 class="text-small font-medium text-ink-1">Button</h3>
    {@render matrix('button')}
    <dl class="rows">
      <div class="row">
        <dt>
          Solid ink only for a person's decision: confirm, allow, approve, sign, apply. One per
          region at most
        </dt>
        <dd>
          <Button variant="decision" icon="sign-off">Sign off CASE-0142</Button>
          <Button variant="decision" icon="check">Apply changes</Button>
          <Button variant="decision">Allow access</Button>
        </dd>
      </div>
      <div class="row">
        <dt>
          The everyday primary is raised and outlined, never filled. Key caps follow the word where
          a shortcut exists
        </dt>
        <dd>
          <Button variant="primary" shortcut={RUN}>Run R2</Button>
          <Button icon="magnifying-glass" shortcut={SEARCH}>Search cases</Button>
          <Button variant="decision" shortcut={RUN}>Apply changes</Button>
          <Button variant="primary" size="small" shortcut={SAVE}>Save draft</Button>
        </dd>
      </div>
      <div class="row">
        <dt>
          Two sizes, ui (14 px) and small (13 px), both on the 8 px control radius; an icon leads or
          trails the word
        </dt>
        <dd>
          <Button icon="download-simple">Export receipt</Button>
          <Button trailingIcon="arrow-up-right">Open CASE-0142</Button>
          <Button size="small" icon="download-simple">Export receipt</Button>
          <Button size="small" trailingIcon="caret-down">More actions</Button>
          <Button size="small" variant="quiet" icon="arrow-clockwise">Re-run R2</Button>
        </dd>
      </div>
      <div class="row">
        <dt>Heights follow the region's density; hit targets stay 24 px or more</dt>
        <dd class="densities">
          {#each DENSITIES as { density, caption } (density)}
            <div class="flex flex-col items-start gap-2" data-density={density}>
              <span class="flex items-center gap-2">
                <Button variant="primary" icon="download-simple">Export receipt</Button>
                <Button size="small">Save draft</Button>
                <IconButton icon="copy" label="Copy case id" variant="secondary" />
              </span>
              <span class="text-caption text-ink-3">{density}: {caption}</span>
            </div>
          {/each}
        </dd>
      </div>
      <div class="row">
        <dt>
          Loading locks the width: the ring takes room the button already holds, so the two below
          are the same width
        </dt>
        <dd>
          <span class="flex flex-col items-start gap-2">
            <Button loading={false}>Save draft</Button>
            {#key ringRun}
              <Button loading>Save draft</Button>
            {/key}
          </span>
          <ReplayButton label="Replay the loading ring" onclick={() => ringRun++} />
        </dd>
      </div>
      <div class="row">
        <dt>
          Press to load for 12 s: the ring after 300 ms, then a tip with the elapsed time after 10 s
        </dt>
        <dd>
          <Button
            variant="primary"
            icon="download-simple"
            loading={exporting}
            onclick={() => load((value) => (exporting = value), 12_000)}
          >
            Export receipt
          </Button>
          <IconButton
            icon="arrow-clockwise"
            label="Refresh CASE-0142"
            variant="secondary"
            loading={refreshing}
            onclick={() => load((value) => (refreshing = value), 3_000)}
          />
        </dd>
      </div>
      <div class="row">
        <dt>An answer inside 300 ms never flashes the ring</dt>
        <dd>
          <Button loading={saving} onclick={() => load((value) => (saving = value), 200)}>
            Save draft
          </Button>
        </dd>
      </div>
      <div class="row">
        <dt>
          Disabled with a reason stays in the tab order: focus or press it to read why. Without one,
          it is skipped
        </dt>
        <dd>
          <Button variant="decision" icon="sign-off" disabled reason="R2 is still running">
            Sign off CASE-0142
          </Button>
          <Button variant="primary" shortcut={RUN} disabled reason="Add a file before running R2">
            Run R2
          </Button>
          <IconButton icon="copy" label="Copy case id" disabled reason="No case is open" />
          <Button disabled>Export receipt</Button>
        </dd>
      </div>
      <div class="row">
        <dt>
          Selected: a toolbar control whose panel is open. Settings that are on or off use the
          worded two-option choice, never a toggle button
        </dt>
        <dd>
          <Button
            variant="quiet"
            icon="funnel"
            pressed={filters}
            onclick={() => (filters = !filters)}
          >
            Filters
          </Button>
          <IconButton
            icon="sidebar-simple"
            label="Side panel"
            pressed={panel}
            onclick={() => (panel = !panel)}
          />
        </dd>
      </div>
      <div class="row">
        <dt>Reduced motion: the ring is its still frame, six dots</dt>
        <dd data-motion="reduce">
          <Button loading icon="download-simple">Export receipt</Button>
          <IconButton icon="arrow-clockwise" label="Refresh CASE-0142" loading />
        </dd>
      </div>
      <div class="row">
        <dt>Hindi: matras stay whole, no capitals, the same width rules</dt>
        <dd lang="hi">
          <Button variant="decision" icon="sign-off">हस्ताक्षर करें</Button>
          <Button variant="primary" shortcut={RUN}>R2 चलाएँ</Button>
          <Button icon="download-simple">रसीद निर्यात करें</Button>
          <Button variant="quiet">सभी नियम दिखाएँ</Button>
          <Button variant="danger">मसौदा हटाएँ</Button>
          <Button size="small" loading>मसौदा सहेजें</Button>
          <Button disabled reason="पहले एक फ़ाइल जोड़ें">रसीद निर्यात करें</Button>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">IconButton</h3>
    {@render matrix('icon')}
    <dl class="rows">
      <div class="row">
        <dt>
          Only in dense toolbars. The label is required: the accessible name and the hint, on hover
          and on focus
        </dt>
        <dd>
          <ButtonGroup label="Case tools">
            <IconButton icon="copy" label="Copy case id" />
            <IconButton icon="download-simple" label="Download receipt" />
            <IconButton
              icon="sidebar-simple"
              label="Side panel"
              pressed={panel}
              onclick={() => (panel = !panel)}
            />
            <IconButton icon="dots-three" label="More actions" />
          </ButtonGroup>
          <IconButton icon="download-simple" label="Download receipt" size="small" />
        </dd>
      </div>
      <div class="row">
        <dt>A shortcut joins the hint as key caps; aria-keyshortcuts announces it</dt>
        <dd>
          <IconButton icon="command" label="Command palette" shortcut={SEARCH} />
          <IconButton icon="magnifying-glass" label="Search cases" variant="secondary">
            {#snippet tooltip()}Search cases, rules and hashes{/snippet}
          </IconButton>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">TextButton and Link</h3>
    <dl class="rows">
      <div class="row">
        <dt>TextButton: an action that reads as text. ink-2, ink-1 with an underline on hover</dt>
        <dd>
          {#each STATES.filter(({ state }) => !['selected', 'loading'].includes(state)) as { state, caption } (state)}
            <span class="preview">
              <TextButton
                data-preview={PREVIEWED.includes(state) ? state : undefined}
                disabled={state === 'disabled'}
                reason={state === 'disabled' ? REASON : undefined}
              >
                Show all rules
              </TextButton>
              <span class="font-mono text-caption text-ink-3">{caption}</span>
            </span>
          {/each}
        </dd>
      </div>
      <div class="row">
        <dt>Beside content, with an icon, and small</dt>
        <dd>
          <span class="text-ui text-ink-2">3 files read, 1 set aside.</span>
          <TextButton trailingIcon="caret-down">Show details</TextButton>
          <TextButton icon="x" size="small">Clear filters</TextButton>
        </dd>
      </div>
      <div class="row">
        <dt>
          Link: ink with a 3:1 underline that firms up on hover; current is the selected recipe
        </dt>
        <dd>
          {#each ['default', 'hover', 'focus', 'active'] as state (state)}
            <span class="preview">
              <Link href="/ui#actions" data-preview={state === 'default' ? undefined : state}
                >R2 limits</Link
              >
              <span class="font-mono text-caption text-ink-3">
                {state === 'focus' ? 'focus-visible' : state}
              </span>
            </span>
          {/each}
          <span class="preview">
            <Link href="/ui#actions" aria-current="page">R2 limits</Link>
            <span class="font-mono text-caption text-ink-3">current</span>
          </span>
        </dd>
      </div>
      <div class="row">
        <dt>In prose it takes the type step around it; an external link carries an arrow</dt>
        <dd>
          <p class="max-w-prose text-body text-ink-2">
            The limit for Ratio comes from <Link href="/ui#actions">rule R2</Link>, and
            <Link href="/ui#actions" class="font-mono">CASE-0142</Link> shows it applied. The format is
            described in the
            <Link href="https://example.org/notes" external externalLabel="leaves 4CE"
              >public notes</Link
            >.
          </p>
        </dd>
      </div>
      <div class="row">
        <dt>Hindi</dt>
        <dd lang="hi">
          <TextButton trailingIcon="caret-down">विवरण दिखाएँ</TextButton>
          <TextButton disabled reason="कोई फ़िल्टर नहीं लगा है">फ़िल्टर हटाएँ</TextButton>
          <span class="text-body text-ink-2">
            सीमा <Link href="/ui#actions">नियम R2</Link> से आती है।
          </span>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Kbd</h3>
    <dl class="rows">
      <div class="row">
        <dt>Combinations: ⌘ on Apple, Ctrl elsewhere; symbols carry a spoken name</dt>
        <dd>
          <Kbd keys={SEARCH} />
          <Kbd keys={RUN} />
          <Kbd keys={['shift', 'enter']} />
          <Kbd keys={['esc']} />
          <Kbd keys={['/']} />
          <Kbd keys={['?']} />
        </dd>
      </div>
      <div class="row">
        <dt>Sequences and movement keys, as the shortcut sheet lists them</dt>
        <dd>
          <span class="inline-flex items-center gap-1 text-caption text-ink-3">
            <Kbd keys={['g']} /> then <Kbd keys={['c']} />
          </span>
          <span class="inline-flex items-center gap-1">
            <Kbd keys={['j']} /><Kbd keys={['k']} />
          </span>
          <span class="inline-flex items-center gap-1">
            <Kbd keys={['left']} /><Kbd keys={['right']} />
          </span>
        </dd>
      </div>
      <div class="row">
        <dt>
          Inside a button the caps take its ink, on every variant; they are hidden from the name and
          aria-keyshortcuts says them instead
        </dt>
        <dd>
          <Button variant="decision" shortcut={RUN}>Apply changes</Button>
          <Button variant="primary" shortcut={RUN}>Run R2</Button>
          <Button variant="quiet" shortcut={SEARCH}>Search cases</Button>
          <Button variant="danger" shortcut={['shift', 'backspace']}>Discard draft</Button>
        </dd>
      </div>
      <div class="row">
        <dt>Hindi: the words follow the language, the legends match the physical keys</dt>
        <dd lang="hi">
          <span class="inline-flex items-center gap-2 text-ui text-ink-2">
            खोजें <Kbd keys={SEARCH} />
          </span>
          <span class="inline-flex items-center gap-2 text-ui text-ink-2">
            बंद करें <Kbd keys={['esc']} />
          </span>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">ButtonGroup</h3>
    <dl class="rows">
      <div class="row">
        <dt>
          One leading-aligned row under the content it acts on, primary first, each named by verb
          and object
        </dt>
        <dd class="stacked">
          <div class="flex flex-col items-start gap-3">
            <p class="text-ui text-ink-2">Draft for CASE-0142: 3 files read, Ratio within R2.</p>
            <ButtonGroup label="Draft">
              <Button variant="primary" shortcut={SAVE}>Save draft</Button>
              <Button icon="download-simple">Export receipt</Button>
              <Button variant="danger">Discard draft</Button>
            </ButtonGroup>
          </div>
          <div class="flex flex-col items-start gap-3">
            <p class="text-ui text-ink-2">2 changes to the R2 limits, reviewed.</p>
            <ButtonGroup label="Changes to R2">
              <Button variant="decision" icon="check">Apply changes</Button>
              <Button variant="quiet">Keep editing</Button>
            </ButtonGroup>
          </div>
        </dd>
      </div>
      <div class="row">
        <dt>
          Attached: one strip, inner corners square; the shared edge goes to the hovered, focused or
          selected one
        </dt>
        <dd>
          <ButtonGroup label="Receipt" attached>
            <Button icon="copy">Copy id</Button>
            <Button icon="download-simple">Download receipt</Button>
            <Button trailingIcon="arrow-up-right">Open CASE-0142</Button>
          </ButtonGroup>
          <ButtonGroup label="Zoom" attached>
            <IconButton icon="minus" label="Zoom out" variant="secondary" />
            <IconButton icon="plus" label="Zoom in" variant="secondary" />
          </ButtonGroup>
        </dd>
      </div>
      <div class="row">
        <dt>Spaced groups wrap when the room runs out, still leading-aligned</dt>
        <dd>
          <div class="narrow">
            <ButtonGroup label="Case actions">
              <Button size="small" variant="primary">Open CASE-0142</Button>
              <Button size="small">Re-run R2</Button>
              <Button size="small" variant="danger">Discard draft</Button>
            </ButtonGroup>
          </div>
        </dd>
      </div>
      <div class="row">
        <dt>Compact region, Hindi labels</dt>
        <dd data-density="compact" lang="hi">
          <ButtonGroup label="मसौदा">
            <Button size="small" variant="primary">मसौदा सहेजें</Button>
            <Button size="small" variant="quiet">संपादन जारी रखें</Button>
          </ButtonGroup>
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
      align-items: center;
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
    align-items: center;
    gap: var(--spacing-3);
    min-width: 0;
  }

  .stacked {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-6);
  }

  .densities {
    align-items: flex-end;
    gap: var(--spacing-6);
  }

  .preview {
    display: inline-flex;
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-1);
  }

  .narrow {
    width: calc(var(--spacing-12) * 5);
  }

  /* Only the table scrolls sideways, never the page. */
  .scroller {
    overflow-x: auto;
  }

  .matrix {
    border-collapse: collapse;
    text-align: start;
  }

  .matrix th,
  .matrix td {
    padding: var(--spacing-2) var(--spacing-3);
    border-top: 1px solid var(--color-line-1);
    text-align: start;
    vertical-align: middle;
  }

  .matrix thead th {
    max-width: calc(var(--spacing-12) * 4);
    border-top: 0;
    vertical-align: bottom;
  }

  .matrix tbody th {
    white-space: nowrap;
  }
</style>
