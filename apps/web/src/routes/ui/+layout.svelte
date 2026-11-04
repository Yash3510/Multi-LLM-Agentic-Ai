<script lang="ts">
  // The /ui shell: a toolbar that drives the real theme, density, motion and locale stores, so the
  // reference always shows what ships. Not linked from the app's navigation.
  import { m } from '$lib/i18n/generated/messages.js';
  import { getLocale, setLocale } from '$lib/i18n/generated/runtime.js';
  import { density, type Density } from '$lib/ui/density.svelte';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import { motion, type MotionSetting } from '$lib/ui/motion.svelte';
  import { theme, type ThemeChoice } from '$lib/ui/theme.svelte';
  import type { LayoutProps } from './$types';
  import { replay } from './replay.svelte';
  import Segmented from './Segmented.svelte';

  type Locale = ReturnType<typeof getLocale>;

  let { children }: LayoutProps = $props();

  // Messages are plain functions, so the toolbar passes the locale it renders in, and the page below
  // is rebuilt on a switch. No reload, so the toolbar keeps focus on the control just used.
  let locale = $state(getLocale());

  function switchLocale(next: Locale) {
    setLocale(next, { reload: false });
    locale = next;
  }

  const o = $derived({ locale });
</script>

<svelte:head>
  <title>{m.ui_title({}, o)} · 4CE</title>
</svelte:head>

<header
  class="z-10 border-b border-line-1 bg-surface-raised lg:sticky lg:top-0"
  aria-label={m.ui_settings({}, o)}
>
  <div class="flex flex-wrap items-center gap-x-6 gap-y-3 px-6 py-3">
    <p class="flex items-baseline gap-2 text-ui">
      <span class="font-semibold text-ink-1">{m.app_name({}, o)}</span>
      <span class="text-ink-3">{m.ui_title({}, o)}</span>
    </p>

    <div class="ms-auto flex flex-wrap items-center gap-x-5 gap-y-3">
      <Segmented
        label={m.theme_label({}, o)}
        name="theme"
        options={[
          { value: 'system', label: m.theme_system({}, o) },
          { value: 'light', label: m.theme_light({}, o) },
          { value: 'dark', label: m.theme_dark({}, o) },
        ]}
        bind:value={() => theme.choice, (value: ThemeChoice) => (theme.choice = value)}
      />
      <Segmented
        label={m.density_label({}, o)}
        name="density"
        options={[
          { value: 'comfortable', label: m.density_comfortable({}, o) },
          { value: 'default', label: m.density_default({}, o) },
          { value: 'compact', label: m.density_compact({}, o) },
        ]}
        bind:value={() => density.value, (value: Density) => (density.value = value)}
      />
      <Segmented
        label={m.motion_label({}, o)}
        name="motion"
        options={[
          { value: 'system', label: m.motion_system({}, o) },
          { value: 'reduce', label: m.motion_reduce({}, o) },
        ]}
        bind:value={() => motion.setting, (value: MotionSetting) => (motion.setting = value)}
      />
      <Segmented
        label={m.locale_label({}, o)}
        name="locale"
        options={[
          { value: 'en', label: m.locale_en({}, o), lang: 'en' },
          { value: 'hi', label: m.locale_hi({}, o), lang: 'hi' },
        ]}
        bind:value={() => locale, switchLocale}
      />
      <button
        type="button"
        class="inline-flex h-8 items-center gap-1.5 rounded-pill border border-line-1 bg-surface-raised px-3 text-small text-ink-1 transition-colors duration-quick hover:border-line-2 hover:bg-surface-hover"
        onclick={replay.run}
      >
        <Icon name="arrow-clockwise" size={16} />
        {m.ui_replay({}, o)}
      </button>
    </div>
  </div>
</header>

{#key locale}
  {@render children()}
{/key}
