<script lang="ts">
  // One run in full at /runs/[runId] (web-screens.md; WP-UI-01, part 1): the rail and status line,
  // the open stage's detail, Cancel while it runs, and once released the receipt, what was checked
  // and the details panel, as in the chat. It reads the run by id and follows it from its last
  // event, through a dropped connection, so it shows the run the chat follows (ADR-0035 §3).
  import { data as source, type RunEvent } from '$lib/data';
  import { ends, watchRun } from '$lib/data/runs';
  import {
    deriveRun,
    formatStageTime,
    RAIL,
    stageDetails,
    type RailStage,
    type StageState,
  } from '$lib/data/stages';
  import { m } from '$lib/i18n/generated/messages.js';
  import AnswerBody from '$lib/ui/components/AnswerBody.svelte';
  import Button from '$lib/ui/components/Button.svelte';
  import CitationDialog from '$lib/ui/components/CitationDialog.svelte';
  import DetailsPanel from '$lib/ui/components/DetailsPanel.svelte';
  import EgressIndicator from '$lib/ui/components/EgressIndicator.svelte';
  import Link from '$lib/ui/components/Link.svelte';
  import ReceiptStrip from '$lib/ui/components/ReceiptStrip.svelte';
  import RunErrorCard from '$lib/ui/components/RunErrorCard.svelte';
  import SourcesBar from '$lib/ui/components/SourcesBar.svelte';
  import StageRail from '$lib/ui/components/StageRail.svelte';
  import StatusLine from '$lib/ui/components/StatusLine.svelte';
  import ToolGroup from '$lib/ui/components/ToolGroup.svelte';
  import TopBar from '$lib/ui/components/TopBar.svelte';
  import { renderMarkdown } from '$lib/ui/markdown';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();

  // The run as shown: as the run store had it when the page opened, then each new event.
  let events = $state<RunEvent[]>([]);
  let finished = $state(false);
  let reconnecting = $state(false);
  let picked = $state<RailStage>();
  let handover = $state<RailStage>();
  let citing = $state<number>();
  let citationOpen = $state(false);

  $effect.pre(() => {
    const run = data.run;
    events = [...run.events];
    finished = run.finished;
    picked = undefined;
    if (run.finished) return;
    const controller = new AbortController();
    void follow(run.id, run.events.at(-1)?.seq ?? 0, controller.signal);
    return () => controller.abort();
  });

  async function follow(id: string, after: number, signal: AbortSignal) {
    const onreconnecting = (state: boolean) => (reconnecting = state);
    for await (const event of watchRun(source, id, after, { signal, onreconnecting })) {
      events.push(event);
      if (ends(event)) finished = true;
    }
  }

  const NAMES: Record<RailStage, string> = {
    planner: 'Planner',
    analyst: 'Analyst',
    author: 'Author',
    challenger: 'Challenger',
    'sign-off': 'Sign-off',
  };
  const STATES: Record<StageState, string> = {
    pending: 'not reached',
    skipped: 'skipped',
    active: 'working',
    interrupted: 'cut off',
    requeued: 'running again',
    fail: 'sent it back',
    released: 'released',
    withheld: 'withheld',
    done: 'done',
  };
  const VERDICTS = { pass: 'PASS', review: 'REVIEW', fail: 'FAIL' } as const;

  const run = $derived(deriveRun(events, finished, Date.now()));
  const details = $derived(stageDetails(events));
  // The open stage: the person's pick, else where the run is.
  const frontier = $derived(
    RAIL.find((stage) => run.stages[stage].state === 'active') ??
      RAIL.findLast((stage) => run.stages[stage].passes > 0) ??
      'planner',
  );
  const shown = $derived(picked ?? frontier);
  const view = $derived(run.stages[shown]);
  const detail = $derived(details[shown]);
  const meta = $derived(
    [
      view.note ?? STATES[view.state],
      // A working stage's time runs on the rail; the detail gives it once the stage is done.
      view.ms > 0 && view.state !== 'active' ? formatStageTime(view.ms) : '',
      view.passes > 1 ? `ran ${view.passes} times` : '',
    ]
      .filter(Boolean)
      .join(' · '),
  );

  const text = $derived(
    events.flatMap((event) => (event.type === 'delta' ? [event.text] : [])).join(''),
  );
  const sources = $derived(RAIL.flatMap((stage) => details[stage].sources));
  const request = $derived(events.findLast((event) => event.type === 'sign-off')?.request);
  const checks = $derived(request?.checks ?? []);
  const decision = $derived(events.findLast((event) => event.type === 'decision'));
  const receipt = $derived(events.findLast((event) => event.type === 'receipt')?.receipt);
  const failure = $derived(events.findLast((event) => event.type === 'error'));
  // The role the run stopped at names the error card; the gate falls back to 4CE.
  const stoppedAt = $derived.by(() => {
    const stage = RAIL.find((item) => run.stages[item].note === 'failed');
    return stage && stage !== 'sign-off' ? NAMES[stage] : undefined;
  });
  // Each status with its offset from the run's start, for the details panel's timeline.
  const steps = $derived.by(() => {
    const start = events[0]?.at ?? 0;
    return events.flatMap((event) =>
      event.type === 'status'
        ? [{ ms: event.at - start, stage: event.stage, text: event.description }]
        : [],
    );
  });

  // As the receipt writes the decision's time.
  const clock = new Intl.DateTimeFormat('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  });

  const cite = (index: number) => {
    citing = index;
    citationOpen = true;
  };
</script>

<svelte:head><title>{`${data.run.question} / ${m.app_name()}`}</title></svelte:head>

<div class="run-view">
  <TopBar title={data.run.question}>
    {#snippet end()}
      <EgressIndicator />
    {/snippet}
  </TopBar>

  <div class="page">
    <h1 class="sr-only">Run: {data.run.question}</h1>
    <p class="back"><Link href={`/c/${data.run.chatId}`}>Open the conversation</Link></p>

    <StageRail
      {events}
      {finished}
      selected={shown}
      onselect={(stage) => (picked = stage)}
      controls="stage-detail"
      onhandover={(role) => (handover = role)}
    />
    <div class="status">
      <StatusLine {events} {finished} {handover} {reconnecting} />
      {#if !finished}
        <Button variant="secondary" size="small" onclick={() => source.cancelRun(data.run.id)}>
          Cancel run
        </Button>
      {/if}
    </div>

    {#if failure}
      <RunErrorCard detail={failure.message} advice={failure.advice} role={stoppedAt} />
    {/if}

    <div
      id="stage-detail"
      class="stage"
      role="tabpanel"
      tabindex="0"
      aria-label={`${NAMES[shown]} details`}
    >
      <div class="body">
        <h2 class="head">
          <span class="name">{NAMES[shown]}</span>
          <span class="meta">{meta}</span>
        </h2>
        {#if detail.lines.length}
          <ol class="lines">
            {#each detail.lines as line, index (index)}
              {#if line.try > 1 && detail.lines[index - 1]?.try !== line.try}
                <li class="try">Try {line.try}</li>
              {/if}
              <li class="line">
                <span class="at">+{(line.ms / 1000).toFixed(1)}s</span>
                <span>{line.text}</span>
              </li>
            {/each}
          </ol>
        {:else}
          <p class="quiet">Waiting for the first step.</p>
        {/if}
        {#if detail.calls.length}<ToolGroup calls={detail.calls} />{/if}
        {#if detail.sources.length}<SourcesBar sources={detail.sources} onopen={cite} />{/if}
        {#if shown === 'author' && detail.text}
          <AnswerBody
            html={renderMarkdown(detail.text, sources)}
            oncite={cite}
            typing={view.state === 'active'}
          />
        {/if}
        {#if shown === 'challenger' && checks.length}
          <ul class="checks" aria-label="What was checked">
            {#each checks as check (check.label)}
              <li>
                <span class="verdict" data-verdict={check.verdict}>{VERDICTS[check.verdict]}</span>
                {check.label}
              </li>
            {/each}
          </ul>
        {/if}
        {#if shown === 'sign-off'}
          {#if decision}
            <p>
              {decision.outcome === 'released' ? 'Released' : 'Withheld'} by {decision.by}, {clock.format(
                new Date(decision.at),
              )}
            </p>
          {:else if request && !finished}
            <p>
              Nothing is released until a person approves it.
              <Link href={`/c/${data.run.chatId}`}>Review it in the conversation</Link>
            </p>
          {/if}
        {/if}
      </div>
    </div>

    {#if receipt && decision?.outcome === 'released'}
      <ReceiptStrip
        {receipt}
        {checks}
        releasedAt={new Date(decision.at)}
        cited={sources.filter((item) => text.includes(`[${item.index}]`)).map((item) => item.title)}
        revision={request?.revision}
      />
      <DetailsPanel folds={receipt.folds} {sources} {checks} answer={text} {steps} onopen={cite} />
    {/if}
    <CitationDialog
      source={sources.find((item) => item.index === citing)}
      bind:open={citationOpen}
    />
  </div>
</div>

<style>
  .run-view {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-block-size: 0;
  }

  .page {
    inline-size: 100%;
    max-inline-size: 928px;
    margin-inline: auto;
    padding: var(--spacing-6) var(--spacing-4) var(--spacing-12);
  }

  .back {
    margin-block-end: var(--spacing-6);
    font-size: var(--text-small);
  }

  .status {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: start;
    gap: var(--spacing-3);
  }

  /* The details panel's surface (ADR-0043): a soft fill around one raised body. */
  .stage {
    margin-block: var(--spacing-4) var(--spacing-2);
    padding: 6px;
    border: 1px solid var(--color-line-1);
    border-radius: var(--radius-panel);
    background-color: var(--glass-soft);
    box-shadow: var(--glass-edge);
    font-size: var(--text-small);
  }

  .stage:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }

  .body {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-3);
    padding: var(--spacing-3) var(--spacing-4);
    border-radius: calc(var(--radius-panel) - 6px);
    background-color: var(--color-surface-raised);
    box-shadow: var(--shadow-hairline);
    color: var(--color-ink-2);
    line-height: 1.5;
  }

  .head {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: var(--spacing-2);
    margin: 0;
    font-size: inherit;
    font-weight: inherit;
  }

  /* As the rail names its nodes. */
  .name,
  .try,
  .verdict {
    font-family: var(--font-mono);
    font-size: var(--text-tag);
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  .name {
    color: var(--color-ink-1);
  }

  .meta,
  .at,
  .try,
  .quiet {
    color: var(--color-ink-3);
  }

  .lines,
  .checks {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .line {
    display: grid;
    grid-template-columns: 52px minmax(0, 1fr);
    gap: var(--spacing-3);
  }

  .at {
    font-family: var(--font-mono);
    font-size: var(--text-tag);
    font-variant-numeric: tabular-nums;
    line-height: 1.9;
  }

  .try:not(:first-child) {
    margin-block-start: var(--spacing-2);
  }

  .checks li {
    display: flex;
    align-items: baseline;
    gap: var(--spacing-2);
  }

  .verdict {
    flex-shrink: 0;
    min-inline-size: 52px;
  }

  .verdict[data-verdict='pass'] {
    color: var(--color-ok);
  }

  .verdict[data-verdict='review'] {
    color: var(--color-caution);
  }

  .verdict[data-verdict='fail'] {
    color: var(--color-stop);
  }
</style>
