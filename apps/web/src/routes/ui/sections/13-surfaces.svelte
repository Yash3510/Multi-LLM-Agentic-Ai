<script module lang="ts">
  import type { SectionMeta } from '../section';

  // English until the ui_section_surfaces and ui_surfaces_* messages exist (requested); the captions
  // below are the same. Demo data is sector-neutral: rule R2, parameter Ratio, ids like CASE-0142.
  export const section: SectionMeta = {
    id: 'surfaces',
    title: () => 'Surfaces',
    description: () =>
      'Cards, panels, dialogs, the side panel, sheets, popovers, tooltips, menus, tabs, disclosures, separators and scroll areas, in every state.',
  };
</script>

<script lang="ts">
  import { getLocale } from '$lib/i18n/generated/runtime.js';
  import Accordion from '$lib/ui/components/Accordion.svelte';
  import Button from '$lib/ui/components/Button.svelte';
  import Card from '$lib/ui/components/Card.svelte';
  import Checkbox from '$lib/ui/components/Checkbox.svelte';
  import Dialog from '$lib/ui/components/Dialog.svelte';
  import Disclosure from '$lib/ui/components/Disclosure.svelte';
  import EmptyState from '$lib/ui/components/EmptyState.svelte';
  import Field from '$lib/ui/components/Field.svelte';
  import IconButton from '$lib/ui/components/IconButton.svelte';
  import InlineAlert from '$lib/ui/components/InlineAlert.svelte';
  import Kbd from '$lib/ui/components/Kbd.svelte';
  import Link from '$lib/ui/components/Link.svelte';
  import Menu from '$lib/ui/components/Menu.svelte';
  import type { MenuEntry } from '$lib/ui/components/menu-model';
  import Panel from '$lib/ui/components/Panel.svelte';
  import Popover from '$lib/ui/components/Popover.svelte';
  import ScrollArea from '$lib/ui/components/ScrollArea.svelte';
  import Separator from '$lib/ui/components/Separator.svelte';
  import Sheet from '$lib/ui/components/Sheet.svelte';
  import SidePanel from '$lib/ui/components/SidePanel.svelte';
  import Skeleton from '$lib/ui/components/Skeleton.svelte';
  import StatusMark, { type Verdict } from '$lib/ui/components/StatusMark.svelte';
  import Tabs, { type TabItem } from '$lib/ui/components/Tabs.svelte';
  import TextInput from '$lib/ui/components/TextInput.svelte';
  import Tooltip from '$lib/ui/components/Tooltip.svelte';
  import {
    formatDuration,
    formatLimit,
    formatMoney,
    formatQuantity,
    toIntlLocale,
  } from '$lib/ui/format';
  import Icon from '$lib/ui/icons/Icon.svelte';

  // The page is rebuilt when the locale changes, so reading it once is enough.
  const o = { locale: toIntlLocale(getLocale()) };

  type Preview = 'hover' | 'focus' | 'active';
  const PREVIEWED: { preview: Preview; caption: string }[] = [
    { preview: 'hover', caption: 'hover' },
    { preview: 'focus', caption: 'focus-visible' },
    { preview: 'active', caption: 'active' },
  ];
  const DENSITIES = ['comfortable', 'default', 'compact'] as const;
  const REASON = 'Waiting for R2 to finish';

  const CASES: { id: string; rule: string; parameter: string; value: string; verdict: Verdict }[] =
    [
      {
        id: 'CASE-0142',
        rule: 'R2',
        parameter: 'Ratio',
        value: formatQuantity(82.5, '%', o),
        verdict: 'pass',
      },
      {
        id: 'CASE-0143',
        rule: 'R3',
        parameter: 'Duration',
        value: formatDuration(12.4, o),
        verdict: 'review',
      },
      {
        id: 'CASE-0144',
        rule: 'R4',
        parameter: 'Cost',
        value: formatMoney(1240.5, o),
        verdict: 'fail',
      },
    ];
  const LEDGER = Array.from({ length: 24 }, (_, index) => ({
    id: `CASE-${String(101 + index).padStart(4, '0')}`,
    value: formatQuantity(70 + ((index * 7) % 30) + 0.5, '%', o),
  }));

  // The side panel: pressing a case opens it beside the list, which stays usable.
  let dockOpen = $state(false);
  let openCase = $state(CASES[0].id);
  const shown = $derived(CASES.find((entry) => entry.id === openCase) ?? CASES[0]);

  function showCase(id: string) {
    openCase = id;
    dockOpen = true;
  }

  // Dialogs and the sheet.
  let renameOpen = $state(false);
  let caseName = $state('Ratio check');
  let applyOpen = $state(false);
  let confirmOpen = $state(false);
  let sheetOpen = $state(false);
  let drafts = $state(3);
  let columns = $state({ rule: true, parameter: true, value: true, verdict: true, owner: false });
  const shownColumns = $derived(Object.values(columns).filter(Boolean).length);

  // The menu: its choices drill in and are applied to the demo below it.
  let menuDensity = $state('default');
  let menuTheme = $state('system');
  let lastAction = $state('Nothing chosen yet');
  const say = (what: string) => () => (lastAction = what);

  const MENU: MenuEntry[] = $derived([
    {
      type: 'group',
      id: 'case',
      label: 'CASE-0142',
      items: [
        {
          id: 'open',
          label: 'Open CASE-0142',
          icon: 'arrow-up-right',
          shortcut: ['mod', 'o'],
          onSelect: say('Opened CASE-0142'),
        },
        {
          id: 'copy',
          label: 'Copy case id',
          icon: 'copy',
          shortcut: ['mod', 'c'],
          onSelect: say('Copied CASE-0142'),
        },
        {
          id: 'rerun',
          label: 'Re-run R2',
          icon: 'arrow-clockwise',
          disabled: true,
          reason: REASON,
        },
      ],
    },
    { type: 'separator' },
    {
      type: 'drill',
      id: 'density',
      label: 'Density',
      icon: 'list',
      items: [
        {
          type: 'choices',
          id: 'density-choice',
          label: 'Density',
          value: menuDensity,
          options: DENSITIES.map((value) => ({
            value,
            label: value[0].toUpperCase() + value.slice(1),
          })),
          onChange: (value) => (menuDensity = value),
        },
      ],
    },
    {
      type: 'drill',
      id: 'theme',
      label: 'Theme',
      icon: 'monitor',
      items: [
        {
          type: 'choices',
          id: 'theme-choice',
          label: 'Theme',
          value: menuTheme,
          options: [
            { value: 'system', label: 'System', icon: 'monitor' },
            { value: 'light', label: 'Light', icon: 'sun' },
            { value: 'dark', label: 'Dark', icon: 'moon' },
          ],
          onChange: (value) => (menuTheme = value),
        },
      ],
    },
    {
      type: 'drill',
      id: 'export',
      label: 'Export receipt',
      icon: 'download-simple',
      items: [
        {
          id: 'pdf',
          label: 'As PDF',
          icon: 'file-text',
          onSelect: say('Exported the receipt as PDF'),
        },
        {
          id: 'docx',
          label: 'As Word document',
          icon: 'file-doc',
          onSelect: say('Exported the receipt as Word'),
        },
        {
          id: 'xlsx',
          label: 'As spreadsheet',
          icon: 'file-xls',
          onSelect: say('Exported the receipt as a spreadsheet'),
        },
      ],
    },
    { type: 'separator' },
    {
      id: 'discard',
      label: 'Discard draft',
      icon: 'x',
      danger: true,
      onSelect: say('Discarded the draft'),
    },
  ]);

  // Tabs, disclosures and accordions.
  let tab = $state('rules');
  const TABS: TabItem[] = [
    { value: 'overview', label: 'Overview' },
    { value: 'rules', label: 'Rules', count: 12 },
    { value: 'evidence', label: 'Evidence', count: 3 },
    { value: 'history', label: 'History', icon: 'case-history' },
    { value: 'sign-off', label: 'Sign-off', disabled: true },
  ];
  const TABS_HI: TabItem[] = [
    { value: 'overview', label: 'सारांश' },
    { value: 'rules', label: 'नियम', count: 12 },
    { value: 'evidence', label: 'साक्ष्य', count: 3 },
  ];
  let accordionOne = $state(['r2']);
  let accordionMany = $state<string[]>([]);
  const RULES = [
    { value: 'r2', label: 'R2 · Ratio', detail: formatLimit('max', 85, '%', o) },
    { value: 'r3', label: 'R3 · Duration', detail: formatLimit('max', 10, 's', o) },
    { value: 'r4', label: 'R4 · Share', detail: formatLimit('min', 20, '%', o) },
    { value: 'r5', label: 'R5 · Ratio', detail: 'No data', disabled: true },
  ];
</script>

{#snippet caseBody(entry: (typeof CASES)[number])}
  <span class="flex items-center justify-between gap-3">
    <span class="font-mono text-caption text-ink-3">{entry.id}</span>
    <StatusMark verdict={entry.verdict} />
  </span>
  <span class="block text-ui font-medium">{entry.rule} · {entry.parameter}</span>
  <span class="block text-small text-ink-2 tabular">{entry.value}</span>
{/snippet}

{#snippet closeHint()}
  <IconButton icon="x" label="Close panel" shortcut={['esc']} />
{/snippet}

<!-- English in every locale until the messages exist, so it says so; the Hindi rows set their own. -->
<div class="flex flex-col gap-10" lang="en">
  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Card</h3>
    <div class="tiles">
      <figure>
        <Card element="article">{@render caseBody(CASES[0])}</Card>
        <figcaption>default · e0, static</figcaption>
      </figure>
      {#each PREVIEWED as { preview, caption } (preview)}
        <figure>
          <Card href="/ui#surfaces" data-preview={preview}>{@render caseBody(CASES[0])}</Card>
          <figcaption>{caption}{preview === 'hover' ? ' · e1' : ''}</figcaption>
        </figure>
      {/each}
      <figure>
        <Card href="/ui#surfaces" selected>{@render caseBody(CASES[1])}</Card>
        <figcaption>selected: the case open beside it</figcaption>
      </figure>
      <figure>
        <Card href="/ui#surfaces" disabled reason={REASON}>{@render caseBody(CASES[2])}</Card>
        <figcaption>disabled, with the reason</figcaption>
      </figure>
      <figure>
        <Card href="/ui#surfaces" loading>
          <span class="flex items-center justify-between gap-3">
            <Skeleton step="caption" class="w-1/3" />
            <Skeleton step="caption" class="w-1/4" />
          </span>
          <Skeleton step="ui" last={60} />
          <Skeleton step="small" last={30} />
        </Card>
        <figcaption>loading: aria-busy, skeletons in the real line heights</figcaption>
      </figure>
      <figure>
        <Card element="section">
          <EmptyState
            icon="observation"
            title="No observations yet"
            detail="Checked CASE-0142 against R2 to R6; none has fired."
          />
        </Card>
        <figcaption>empty</figcaption>
      </figure>
      <figure>
        <Card element="section" invalid>
          <InlineAlert tone="stop" title="Could not load CASE-0145">
            The server did not answer within 10 s.
            {#snippet action()}
              <Button size="small" icon="arrow-clockwise">Retry loading</Button>
            {/snippet}
          </InlineAlert>
        </Card>
        <figcaption>error: said in place, a stop edge</figcaption>
      </figure>
    </div>
    <dl class="rows">
      <div class="row">
        <dt>
          A button card is a toggle when it can be chosen; it holds spans, never other controls
        </dt>
        <dd>
          {#each CASES as entry (entry.id)}
            <div class="pick">
              <Card onclick={() => (openCase = entry.id)} selected={openCase === entry.id}>
                {@render caseBody(entry)}
              </Card>
            </div>
          {/each}
        </dd>
      </div>
      <div class="row">
        <dt>Densities change the rows inside, not the card's 16 px inset</dt>
        <dd class="top">
          {#each DENSITIES as density (density)}
            <div class="pick flex flex-col gap-2" data-density={density}>
              <Card href="/ui#surfaces">{@render caseBody(CASES[0])}</Card>
              <span class="text-caption text-ink-3">{density}</span>
            </div>
          {/each}
        </dd>
      </div>
      <div class="row" lang="hi">
        <dt>हिन्दी: मात्राएँ कटती नहीं, बड़े अक्षर नहीं</dt>
        <dd>
          <div class="pick">
            <Card href="/ui#surfaces">
              <span class="font-mono text-caption text-ink-3">CASE-0142</span>
              <span class="block text-ui font-medium">R2 · अनुपात की जाँच</span>
              <span class="block text-small text-ink-2">कल 14:05 IST पर अद्यतन</span>
            </Card>
          </div>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Panel</h3>
    <dl class="rows">
      <div class="row">
        <dt>
          e3 on the 20 px panel radius: title, close with its Esc hint, a body that scrolls on its
          own, and the actions in one leading row, primary first
        </dt>
        <dd>
          <div class="stage">
            <Panel
              style="flex: 1 1 auto"
              title="CASE-0142"
              description="R2 · Ratio, checked at 14:05 IST"
              headerEnd={closeHint}
            >
              <div class="flex flex-col gap-3">
                <StatusMark verdict="pass" variant="badge" />
                <p class="text-body text-ink-2">
                  Ratio {CASES[0].value} against a limit of {formatLimit('max', 85, '%', o)}. The
                  three inputs agree with the receipt.
                </p>
              </div>
              {#snippet actions()}
                <Button variant="primary" icon="download-simple">Export receipt</Button>
                <Button>Copy case id</Button>
              {/snippet}
            </Panel>
          </div>
          <div class="stage short">
            <Panel
              style="flex: 1 1 auto"
              title="Ledger"
              description="24 entries"
              headerEnd={closeHint}
            >
              <ul class="flex flex-col">
                {#each LEDGER as row (row.id)}
                  <li class="flex justify-between border-b border-line-1 py-2 text-small">
                    <span class="font-mono text-ink-2">{row.id}</span>
                    <span class="tabular">{row.value}</span>
                  </li>
                {/each}
              </ul>
            </Panel>
          </div>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Dialog and sheet</h3>
    <dl class="rows">
      <div class="row">
        <dt>
          Still: a flat scrim (graphite at 45 %, 65 % in dark), the dialog at e3. Only for real
          decisions, short forms, stepped flows and re-authentication
        </dt>
        <dd>
          <div class="frame" aria-hidden="true">
            <div class="flex flex-col gap-2 p-4">
              <Skeleton step="title" class="w-1/3" />
              <Skeleton step="body" lines={3} />
            </div>
            <div class="still-scrim" data-surface="scrim"></div>
            <div class="still-dialog">
              <Panel element="div" title="Rename CASE-0142" headerEnd={closeHint}>
                <p class="text-small text-ink-2">The new name shows on the receipt.</p>
                {#snippet actions()}
                  <Button variant="primary" tabindex={-1}>Rename case</Button>
                  <Button tabindex={-1}>Cancel</Button>
                {/snippet}
              </Panel>
            </div>
          </div>
        </dd>
      </div>
      <div class="row">
        <dt>
          A short form. Focus starts in the field, stays inside, and returns to the button; Esc or a
          press on the scrim closes
        </dt>
        <dd>
          <Dialog bind:open={renameOpen} title="Rename CASE-0142" closeLabel="Close" size="small">
            {#snippet trigger({ props })}
              <Button {...props}>Rename CASE-0142</Button>
            {/snippet}
            <Field label="Case name" description="Shown on the receipt and in the ledger">
              <TextInput bind:value={caseName} data-autofocus />
            </Field>
            {#snippet actions({ close })}
              <Button variant="primary" onclick={close}>Rename case</Button>
              <Button onclick={close}>Cancel</Button>
            {/snippet}
          </Dialog>
          <span class="text-small text-ink-2">Name: {caseName}</span>
        </dd>
      </div>
      <div class="row">
        <dt>
          A decision that must not vanish by accident: a press on the scrim does nothing; Esc and
          the buttons still close. The decision is ink, never violet
        </dt>
        <dd>
          <Dialog
            bind:open={applyOpen}
            title="Apply 3 rule changes"
            description="R2, R3 and R4 take their new limits from the next run."
            closeLabel="Close"
            dismissible={false}
          >
            {#snippet trigger({ props })}
              <Button {...props}>Review 3 rule changes</Button>
            {/snippet}
            <ul class="flex flex-col gap-1 text-small text-ink-2">
              <li>R2 · Ratio {formatLimit('max', 85, '%', o)}</li>
              <li>R3 · Duration {formatLimit('max', 10, 's', o)}</li>
              <li>R4 · Share {formatLimit('min', 20, '%', o)}</li>
            </ul>
            {#snippet actions({ close })}
              <Button variant="decision" icon="check" onclick={close}>Apply changes</Button>
              <Button onclick={close}>Keep editing</Button>
            {/snippet}
          </Dialog>
        </dd>
      </div>
      <div class="row">
        <dt>
          Confirm only what cannot be undone, naming the consequence. Focus starts on the dismiss,
          Enter is ignored, the scrim never closes it
        </dt>
        <dd>
          <Dialog
            bind:open={confirmOpen}
            role="alertdialog"
            size="small"
            title="Delete {drafts} drafts?"
            description="The drafts of R2, R3 and R4 are removed for everyone. This cannot be undone."
            closeLabel="Close"
          >
            {#snippet trigger({ props })}
              <Button {...props} variant="danger" disabled={drafts === 0}
                >Delete {drafts} drafts</Button
              >
            {/snippet}
            <p class="text-small text-ink-2">Published rules are not affected.</p>
            {#snippet actions({ close })}
              <Button variant="danger" onclick={() => ((drafts = 0), close())}
                >Delete {drafts} drafts</Button
              >
              <Button data-dismiss onclick={close}>Keep drafts</Button>
            {/snippet}
          </Dialog>
          {#if drafts === 0}
            <Button
              size="small"
              variant="quiet"
              icon="arrow-clockwise"
              onclick={() => (drafts = 3)}
            >
              Bring the demo drafts back
            </Button>
          {/if}
        </dd>
      </div>
      <div class="row">
        <dt>A sheet docks to the bottom edge, up to 960 px wide, for pickers and short forms</dt>
        <dd>
          <Sheet
            bind:open={sheetOpen}
            title="Choose columns"
            description="For the cases table"
            closeLabel="Close"
          >
            {#snippet trigger({ props })}
              <Button {...props} icon="list">Choose columns</Button>
            {/snippet}
            <Field label="Columns" group>
              <Checkbox label="Rule" bind:checked={columns.rule} />
              <Checkbox label="Parameter" bind:checked={columns.parameter} />
              <Checkbox label="Value" bind:checked={columns.value} />
              <Checkbox label="Verdict" bind:checked={columns.verdict} />
              <Checkbox label="Owner" bind:checked={columns.owner} />
            </Field>
            {#snippet actions({ close })}
              <Button variant="primary" onclick={close}>Show {shownColumns} columns</Button>
              <Button onclick={close}>Cancel</Button>
            {/snippet}
          </Sheet>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Side panel</h3>
    <p class="max-w-prose text-small text-ink-2">
      Where everyday tasks open. On a desktop it docks beside the page, which reflows and stays
      usable; on a tablet it is a full-height layer on the right edge. No scrim and no trap: Esc
      closes it while focus is inside, and focus goes back to what opened it.
    </p>
    <div class="desk">
      <div class="desk-page">
        <p class="text-small text-ink-2">Press a case to open it beside the list.</p>
        {#each CASES as entry (entry.id)}
          <Card onclick={() => showCase(entry.id)} selected={dockOpen && openCase === entry.id}>
            {@render caseBody(entry)}
          </Card>
        {/each}
      </div>
      <SidePanel
        bind:open={dockOpen}
        title={shown.id}
        description="{shown.rule} · {shown.parameter}"
        closeLabel="Close panel"
      >
        <div class="flex flex-col gap-4">
          <StatusMark verdict={shown.verdict} variant="badge" />
          <dl class="facts">
            <dt>Value</dt>
            <dd class="tabular">{shown.value}</dd>
            <dt>Rule</dt>
            <dd>{shown.rule}</dd>
            <dt>Checked</dt>
            <dd>14:05 IST</dd>
          </dl>
          <Disclosure label="Show the inputs" detail="3 inputs">
            <p class="text-small text-ink-2">
              Two readings and one limit, each with its source page.
            </p>
          </Disclosure>
        </div>
        {#snippet actions({ close })}
          <Button variant="primary" icon="download-simple">Export receipt</Button>
          <Button onclick={close}>Close {shown.id}</Button>
        {/snippet}
      </SidePanel>
    </div>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Popover and tooltip</h3>
    <dl class="rows">
      <div class="row">
        <dt>Stills: a popover at e2 on the card radius, a tooltip at e2 on the control radius</dt>
        <dd class="top">
          <div class="still-float" data-surface="float" aria-hidden="true">
            <p class="text-ui font-medium">Inputs for R2</p>
            <p class="text-small text-ink-2 tabular">
              Ratio {CASES[0].value} · limit {formatLimit('max', 85, '%', o)}
            </p>
          </div>
          <div class="still-tip" data-surface="tip" aria-hidden="true">
            <span class="flex items-center gap-2">Copy the case id <Kbd keys={['mod', 'c']} /></span
            >
          </div>
        </dd>
      </div>
      <div class="row">
        <dt>
          Hover for 280 ms or focus by key to peek; 160 ms of grace before it closes. Enter, Space
          or ↓ steps into it, a press opens it for real, Esc closes
        </dt>
        <dd>
          <Popover label="Inputs for R2" icon="calculation" title="Inputs for R2">
            <dl class="facts">
              <dt>Ratio</dt>
              <dd class="tabular">{CASES[0].value}</dd>
              <dt>Limit</dt>
              <dd class="tabular">{formatLimit('max', 85, '%', o)}</dd>
              <dt>Duration</dt>
              <dd class="tabular">{formatDuration(3.7, o)}</dd>
            </dl>
            <span class="text-small"><Link href="/ui#surfaces">Open CASE-0142</Link></span>
          </Popover>
          <Popover label="Filter cases" icon="funnel" peek={false} title="Filter cases">
            <Checkbox label="Needs review" checked />
            <Checkbox label="Failed" />
          </Popover>
          <Popover label="CASE-0143" title="CASE-0143">
            {#snippet trigger({ props })}
              <button {...props} type="button" class="id-link font-mono text-small"
                >CASE-0143</button
              >
            {/snippet}
            <span class="flex items-center gap-2">
              <StatusMark verdict="review" />
              <span class="text-small text-ink-2">R3 · Duration {CASES[1].value}</span>
            </span>
          </Popover>
          <Popover label="Evidence" icon="eye" disabled>
            <p>Unavailable</p>
          </Popover>
        </dd>
      </div>
      <div class="row">
        <dt>
          A tooltip is a hint, opened by focus as well as hover, never a title attribute. A term
          becomes focusable to carry one
        </dt>
        <dd>
          <Tooltip text="Copy the case id" shortcut={['mod', 'c']}>
            {#snippet children({ props })}
              <button
                {...props}
                type="button"
                data-action="icon"
                data-variant="quiet"
                data-size="ui"
                aria-label="Copy CASE-0142"
              >
                <Icon name="copy" size={20} />
              </button>
            {/snippet}
          </Tooltip>
          <span class="text-small text-ink-2">
            Checked at 14:05 <Tooltip label="IST" text="India Standard Time, UTC+05:30" />
          </span>
          <span class="text-small text-ink-2">
            Fingerprint <Tooltip
              label="3f9a21c0…"
              text="The first 8 of 64 hex characters"
              side="bottom"
            />
          </span>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Menu</h3>
    <dl class="rows">
      <div class="row">
        <dt>
          Still, every row state: icon plus word, key caps, the pointer's hover, the keyboard's
          focus, a press, a chosen option, a drill row with its value, a reason, a destructive row
        </dt>
        <dd class="top">
          <div class="still-menu" data-surface="float" data-menu aria-hidden="true">
            <div data-menu-heading>CASE-0142</div>
            <div data-menu-row>
              <span data-menu-lead><Icon name="arrow-up-right" size={16} /></span>
              <span data-menu-text><span data-menu-label>Open CASE-0142 · default</span></span>
              <Kbd keys={['mod', 'o']} />
            </div>
            <div data-menu-row data-highlighted>
              <span data-menu-lead><Icon name="copy" size={16} /></span>
              <span data-menu-text><span data-menu-label>Copy case id · hover</span></span>
              <Kbd keys={['mod', 'c']} />
            </div>
            <div data-menu-row data-highlighted data-preview="focus">
              <span data-menu-lead><Icon name="download-simple" size={16} /></span>
              <span data-menu-text><span data-menu-label>Export receipt · focus</span></span>
            </div>
            <div data-menu-row data-preview="active">
              <span data-menu-lead><Icon name="arrow-clockwise" size={16} /></span>
              <span data-menu-text><span data-menu-label>Re-run R3 · active</span></span>
            </div>
            <div data-menu-row data-disabled>
              <span data-menu-lead><Icon name="arrow-clockwise" size={16} /></span>
              <span data-menu-text>
                <span data-menu-label>Re-run R2 · disabled</span>
                <span data-menu-reason>{REASON}</span>
              </span>
            </div>
            <div data-menu-separator></div>
            <div data-menu-row>
              <span data-menu-lead><Icon name="list" size={16} /></span>
              <span data-menu-text><span data-menu-label>Density</span></span>
              <span data-menu-hint>Default</span>
              <span data-menu-trail><Icon name="caret-right" size={16} /></span>
            </div>
            <div data-menu-row data-danger>
              <span data-menu-lead><Icon name="x" size={16} /></span>
              <span data-menu-text><span data-menu-label>Discard draft</span></span>
            </div>
          </div>
          <div class="still-menu" data-surface="float" data-menu aria-hidden="true">
            <div data-menu-row data-back>
              <span data-menu-lead><Icon name="arrow-left" size={16} /></span>
              <span data-menu-text><span data-menu-label>Density</span></span>
            </div>
            <div data-menu-separator></div>
            <div data-menu-row>
              <span data-menu-text><span data-menu-label>Comfortable</span></span>
              <span data-menu-trail></span>
            </div>
            <div data-menu-row data-checked>
              <span data-menu-text><span data-menu-label>Default · chosen</span></span>
              <span data-menu-trail><Icon name="check" size={16} /></span>
            </div>
            <div data-menu-row>
              <span data-menu-text><span data-menu-label>Compact</span></span>
              <span data-menu-trail></span>
            </div>
          </div>
        </dd>
      </div>
      <div class="row">
        <dt>
          Live. ↑ ↓ move, letters find, Enter chooses. → or a press drills into Density, Theme or
          Export; ← or the back row comes out. No flyouts
        </dt>
        <dd>
          <Menu label="Case actions" icon="dots-three" items={MENU} backLabel="Back" />
          <Menu
            label="More"
            variant="quiet"
            size="small"
            align="end"
            items={MENU}
            backLabel="Back"
          />
          <Menu label="Case actions" items={MENU} backLabel="Back" disabled />
          <span class="text-small text-ink-2" aria-live="polite">
            {lastAction} · density {menuDensity} · theme {menuTheme}
          </span>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Tabs</h3>
    <dl class="rows">
      <div class="row">
        <dt>
          One tab stop; ← → move and the panel follows. Current carries a 2 px ink edge; a disabled
          tab is skipped
        </dt>
        <dd class="full">
          <Tabs tabs={TABS} bind:value={tab} label="Case views">
            {#snippet panel(item)}
              <p class="text-small text-ink-2">
                {item.label} of CASE-0142{item.count !== undefined ? `: ${item.count} items` : ''}.
              </p>
            {/snippet}
          </Tabs>
        </dd>
      </div>
      <div class="row">
        <dt>hover, focus-visible and active, drawn still; small size</dt>
        <dd class="full">
          <Tabs
            label="States"
            size="small"
            value="current"
            tabs={[
              { value: 'current', label: 'Current' },
              ...PREVIEWED.map(({ preview, caption }) => ({
                value: preview,
                label: caption,
                preview,
              })),
              { value: 'disabled', label: 'Disabled', disabled: true },
            ]}
          >
            {#snippet panel(item)}<span class="sr-only">{item.label}</span>{/snippet}
          </Tabs>
        </dd>
      </div>
      <div class="row">
        <dt>Densities set the row height: 40, 32 and 28 px</dt>
        <dd class="stack">
          {#each DENSITIES as density (density)}
            <div data-density={density}>
              <Tabs tabs={TABS.slice(0, 3)} value="rules" label="Case views, {density}">
                {#snippet panel()}<span class="sr-only">{density}</span>{/snippet}
              </Tabs>
            </div>
          {/each}
        </dd>
      </div>
      <div class="row" lang="hi">
        <dt>हिन्दी</dt>
        <dd class="full">
          <Tabs tabs={TABS_HI} value="overview" label="मामले के दृश्य">
            {#snippet panel(item)}<p class="text-small text-ink-2">
                {item.label}: CASE-0142
              </p>{/snippet}
          </Tabs>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Disclosure and accordion</h3>
    <dl class="rows">
      <div class="row">
        <dt>
          Opens by grid rows at calm and closes in two thirds of that, so nothing jumps; the caret
          swaps, it never rotates
        </dt>
        <dd class="full">
          <Disclosure label="Show the inputs" detail="3 inputs">
            <p class="text-small text-ink-2">
              Ratio {CASES[0].value}, measured twice, against a limit of
              {formatLimit('max', 85, '%', o)}. Each input links to its source page.
            </p>
          </Disclosure>
        </dd>
      </div>
      <div class="row">
        <dt>hover, focus-visible, active and disabled, drawn still</dt>
        <dd class="stack">
          {#each PREVIEWED as { preview, caption } (preview)}
            <Disclosure label="Show the inputs · {caption}" detail="3 inputs" {preview}>
              <p class="text-small text-ink-2">Inputs.</p>
            </Disclosure>
          {/each}
          <Disclosure label="Show the inputs · disabled" detail="No inputs yet" disabled>
            <p class="text-small text-ink-2">Inputs.</p>
          </Disclosure>
        </dd>
      </div>
      <div class="row">
        <dt>Accordion, one open at a time. ↑ ↓ move between headings, Home and End jump</dt>
        <dd class="full">
          <Accordion items={RULES} type="single" bind:value={accordionOne} level={4}>
            {#snippet item(rule)}
              <p class="text-small text-ink-2">
                {rule.label}: fires when the value passes {rule.detail}.
              </p>
            {/snippet}
          </Accordion>
        </dd>
      </div>
      <div class="row">
        <dt>Accordion, several open</dt>
        <dd class="full">
          <Accordion items={RULES} bind:value={accordionMany} level={4}>
            {#snippet item(rule)}
              <p class="text-small text-ink-2">
                {rule.label}: fires when the value passes {rule.detail}.
              </p>
            {/snippet}
          </Accordion>
        </dd>
      </div>
      <div class="row" lang="hi">
        <dt>हिन्दी</dt>
        <dd class="full">
          <Disclosure label="इनपुट दिखाएँ" detail="3 इनपुट" open>
            <p class="text-small text-ink-2">अनुपात {CASES[0].value}, दो बार मापा गया।</p>
          </Disclosure>
        </dd>
      </div>
    </dl>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">Separator and scroll area</h3>
    <dl class="rows">
      <div class="row">
        <dt>A line-1 hairline, across or upright; decorative unless it carries structure</dt>
        <dd>
          <span class="flex items-center gap-2">
            <Button size="small" variant="quiet" icon="copy">Copy case id</Button>
            <Separator orientation="vertical" decorative={false} />
            <Button size="small" variant="quiet" icon="download-simple">Export receipt</Button>
          </span>
          <span class="flex w-full flex-col gap-2">
            <span class="text-small text-ink-2">Inputs</span>
            <Separator />
            <span class="text-small text-ink-2">Checks</span>
          </span>
        </dd>
      </div>
      <div class="row">
        <dt>
          A stable gutter, so nothing shifts when the bar appears; a hairline at each edge with more
          beyond. It joins the tab order only while it scrolls
        </dt>
        <dd class="top">
          <div class="scroll-demo">
            <ScrollArea label="Ledger entries" maxBlockSize="12rem">
              <ul class="flex flex-col">
                {#each LEDGER as row (row.id)}
                  <li class="flex justify-between px-3 py-2 text-small">
                    <span class="font-mono text-ink-2">{row.id}</span>
                    <span class="tabular">{row.value}</span>
                  </li>
                {/each}
              </ul>
            </ScrollArea>
          </div>
          <div class="scroll-demo wide">
            <ScrollArea label="Rules" orientation="horizontal">
              <span class="flex gap-2 p-2">
                {#each LEDGER.slice(0, 12) as row (row.id)}
                  <span class="chip font-mono text-caption">{row.id}</span>
                {/each}
              </span>
            </ScrollArea>
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
      align-items: center;
    }
  }

  .row > dt {
    font-size: var(--text-caption);
    line-height: var(--text-caption--line-height);
    color: var(--color-ink-3);
  }

  .row > dd {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--spacing-3);
    min-width: 0;
  }

  .row > dd.top {
    align-items: flex-start;
  }

  .row > dd.stack {
    flex-direction: column;
    align-items: stretch;
  }

  .row > dd.full {
    display: block;
  }

  /* The card matrix: one tile per state, with its caption under it. */
  .tiles {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(calc(var(--spacing-12) * 5), 1fr));
    gap: var(--spacing-4);
  }

  figure {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
    margin: 0;
  }

  figcaption {
    color: var(--color-ink-3);
    font-family: var(--font-mono);
    font-size: var(--text-caption);
    line-height: var(--text-caption--line-height);
  }

  .pick {
    inline-size: calc(var(--spacing-12) * 5);
  }

  /* Panels drawn in place, at a fixed size so the second one scrolls. */
  .stage {
    display: flex;
    flex-direction: column;
    inline-size: min(calc(var(--spacing-12) * 8), 100%);
  }

  .stage.short {
    block-size: calc(var(--spacing-12) * 6);
  }

  /* A still of a dialog over its page, inside a box rather than over the whole page. */
  .frame {
    position: relative;
    inline-size: min(calc(var(--spacing-12) * 12), 100%);
    block-size: calc(var(--spacing-12) * 6);
    border: 1px solid var(--color-line-1);
    border-radius: var(--radius-card);
    background-color: var(--color-surface-page);
    overflow: hidden;
  }

  .still-scrim {
    position: absolute;
    z-index: auto;
  }

  .still-dialog {
    position: absolute;
    inset: var(--spacing-8) var(--spacing-10);
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  /* The side panel's demo row: the page and the dock, side by side on a desktop. */
  .desk {
    display: flex;
    gap: var(--spacing-4);
    block-size: calc(var(--spacing-12) * 11);
    padding: var(--spacing-3);
    border: 1px solid var(--color-line-1);
    border-radius: var(--radius-card);
    background-color: var(--color-surface-page);
  }

  .desk-page {
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
    gap: var(--spacing-3);
    min-inline-size: 0;
    max-inline-size: calc(var(--spacing-12) * 8);
  }

  .facts {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: var(--spacing-1) var(--spacing-4);
    font-size: var(--text-small);
    line-height: var(--text-small--line-height);
  }

  .facts dt {
    color: var(--color-ink-3);
  }

  .facts dd {
    color: var(--color-ink-1);
  }

  .still-float {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);
    padding: var(--spacing-inset-card);
  }

  .still-menu {
    inline-size: calc(var(--spacing-12) * 6);
  }

  /* A case id that peeks: text with a line-control underline, focusable like a link. */
  .id-link {
    border-radius: var(--radius-tight);
    color: var(--color-ink-1);
    text-decoration-line: underline;
    text-decoration-color: var(--color-line-control);
    text-underline-offset: 0.25em;
    cursor: pointer;
  }

  .scroll-demo {
    inline-size: calc(var(--spacing-12) * 6);
    border: 1px solid var(--color-line-1);
    border-radius: var(--radius-inset);
    overflow: hidden;
  }

  .scroll-demo.wide {
    inline-size: calc(var(--spacing-12) * 7);
  }

  .chip {
    padding: var(--spacing-1) var(--spacing-2);
    border: 1px solid var(--color-line-1);
    border-radius: var(--radius-control);
    color: var(--color-ink-2);
    white-space: nowrap;
  }
</style>
