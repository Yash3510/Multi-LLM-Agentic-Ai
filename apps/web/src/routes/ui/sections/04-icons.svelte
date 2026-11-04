<script module lang="ts">
  import { m } from '$lib/i18n/generated/messages.js';
  import type { SectionMeta } from '../section';

  export const section: SectionMeta = {
    id: 'icons',
    title: m.ui_section_icons,
    description: m.ui_icons_intro,
  };
</script>

<script lang="ts">
  import { tick, untrack } from 'svelte';
  import StatusMark, { type Verdict } from '$lib/ui/components/StatusMark.svelte';
  import type { IconName } from '$lib/ui/icons/generated/icons';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import registry from '$lib/ui/icons/registry.json';
  import ReplayButton from '../ReplayButton.svelte';
  import { replay } from '../replay.svelte';

  const ALL = Object.entries(registry).map(([name, entry]) => ({
    name: name as IconName,
    // The Phosphor file, with its weight when the running app draws that place bold.
    glyph: 'weight' in entry ? `${entry.phosphor} · ${entry.weight}` : entry.phosphor,
  }));

  const CONCEPTS: { name: IconName; concept: () => string; verdict?: Verdict }[] = [
    { name: 'verdict-pass', concept: m.ui_concept_verdict_pass, verdict: 'pass' },
    { name: 'verdict-review', concept: m.ui_concept_verdict_review, verdict: 'review' },
    { name: 'verdict-fail', concept: m.ui_concept_verdict_fail, verdict: 'fail' },
    { name: 'verdict-no-data', concept: m.ui_concept_verdict_no_data, verdict: 'no-data' },
    { name: 'unverified', concept: m.ui_concept_unverified, verdict: 'unverified' },
    { name: 'rule', concept: m.ui_concept_rule },
    { name: 'observation', concept: m.ui_concept_observation },
    { name: 'observation-unsure', concept: m.ui_concept_observation_unsure },
    { name: 'pack', concept: m.ui_concept_pack },
    { name: 'skill', concept: m.ui_concept_skill },
    { name: 'ledger', concept: m.ui_concept_ledger },
    { name: 'evidence-pack', concept: m.ui_concept_evidence_pack },
    { name: 'sign-off', concept: m.ui_concept_sign_off },
    { name: 'sign-off-pending', concept: m.ui_concept_sign_off_pending },
    { name: 'sign-off-returned', concept: m.ui_concept_sign_off_returned },
    { name: 'challenger', concept: m.ui_concept_challenger },
  ];

  const SIZES = [16, 18, 24];

  // A replay remounts a verdict with live off, then turns it on: the change StatusMark treats as
  // "seen live".
  let generation = $state<Partial<Record<IconName, number>>>({});
  let live = $state<Partial<Record<IconName, boolean>>>({});

  async function play(name: IconName) {
    generation[name] = (generation[name] ?? 0) + 1;
    live[name] = false;
    await tick();
    live[name] = true;
  }

  $effect(() => {
    if (replay.count > 0)
      untrack(() => CONCEPTS.forEach(({ name, verdict }) => verdict && play(name)));
  });
</script>

<div class="flex flex-col gap-10">
  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">{m.ui_icons_signature()}</h3>
    <div class="overflow-x-auto">
      <table class="w-full border-collapse text-left">
        <thead class="text-caption text-ink-3">
          <tr>
            <th scope="col" class="h-8 pe-4 font-normal">{m.ui_icons_glyph()}</th>
            <th scope="col" class="h-8 pe-4 font-normal tabular">{m.ui_icons_sizes()}</th>
            <th scope="col" class="h-8 pe-4 font-normal">{m.ui_icons_state()}</th>
            <th scope="col" class="h-8 w-6"><span class="sr-only">{m.ui_replay()}</span></th>
          </tr>
        </thead>
        <tbody>
          {#each CONCEPTS as { name, concept, verdict } (name)}
            <tr class="border-t border-line-1">
              <th scope="row" class="py-3 pe-4 font-normal">
                <code class="block font-mono text-small text-ink-1">{name}</code>
                <span class="text-caption text-ink-3">{concept()}</span>
              </th>
              <td class="py-3 pe-4">
                <span class="flex items-end gap-4 text-ink-1">
                  {#each SIZES as size (size)}
                    <Icon {name} {size} />
                  {/each}
                </span>
              </td>
              <td class="py-3 pe-4">
                {#if verdict}
                  {#key generation[name]}
                    <StatusMark {verdict} variant="badge" live={live[name] ?? false} />
                  {/key}
                {/if}
              </td>
              <td class="py-3 align-middle">
                {#if verdict}
                  <ReplayButton label={m.ui_replay_one({ name })} onclick={() => play(name)} />
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>

  <div class="flex flex-col gap-3">
    <h3 class="text-small font-medium text-ink-1">{m.ui_icons_phosphor()}</h3>
    <ul class="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-6">
      {#each ALL as { name, glyph } (name)}
        <li class="flex min-w-0 flex-col gap-3 rounded-inset bg-surface-raised p-3 shadow-hairline">
          <span class="flex items-end gap-3 text-ink-1">
            <Icon {name} size={16} />
            <Icon {name} size={18} />
            <Icon {name} size={24} />
          </span>
          <span class="flex min-w-0 flex-col">
            <code class="font-mono break-all text-caption text-ink-1">{name}</code>
            {#if glyph !== name}
              <code class="font-mono break-all text-caption text-ink-3">{glyph}</code>
            {/if}
          </span>
        </li>
      {/each}
    </ul>
  </div>
</div>
