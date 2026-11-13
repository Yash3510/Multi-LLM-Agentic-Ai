<script lang="ts">
  // Evaluations (admin look §13a): Leaderboard and Feedback with their counts.
  import { data as source } from '$lib/data';
  import { leaderboardRows } from '$lib/ui/evaluations';
  import AdminSection from '$lib/ui/components/AdminSection.svelte';
  import FeedbackList from '$lib/ui/components/FeedbackList.svelte';
  import Leaderboard from '$lib/ui/components/Leaderboard.svelte';
  import type { PageProps } from './$types';

  let { data }: PageProps = $props();

  let models = $state<number>();
  let feedback = $state<number>();

  void Promise.all([source.listBaseModels(), source.leaderboard(), source.listFeedback()]).then(
    ([all, entries, records]) => {
      models = leaderboardRows(all, entries).length;
      feedback = records.length;
    },
  );
</script>

<AdminSection
  label="Evaluations"
  roomy
  items={[
    {
      href: '/admin/evaluations/leaderboard',
      label: 'Leaderboard',
      count: models,
      current: data.tab === 'leaderboard',
    },
    {
      href: '/admin/evaluations/feedback',
      label: 'Feedback',
      count: feedback,
      current: data.tab === 'feedback',
    },
  ]}
>
  {#if data.tab === 'leaderboard'}
    <Leaderboard {source} oncount={(count) => (models = count)} />
  {:else}
    <FeedbackList {source} oncount={(count) => (feedback = count)} />
  {/if}
</AdminSection>
