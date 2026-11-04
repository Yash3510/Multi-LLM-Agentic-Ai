<script lang="ts">
  import { resolve } from '$app/paths';
  import { m } from '$lib/i18n/generated/messages.js';
  import Icon from '$lib/ui/icons/Icon.svelte';
</script>

<main class="mx-auto flex max-w-prose flex-col gap-3 px-6 py-12">
  <h1 class="text-heading text-ink-1">{m.app_name()}</h1>
  <p class="text-body text-ink-2">{m.home_intro()}</p>
  <a
    class="inline-flex items-center gap-1.5 self-start rounded-tight text-ui font-medium text-ink-1 underline decoration-line-control underline-offset-4 transition-colors duration-quick hover:decoration-ink-1"
    href={resolve('/ui')}
  >
    {m.home_ui_link()}
    <Icon name="arrow-up-right" size={16} />
  </a>
</main>
