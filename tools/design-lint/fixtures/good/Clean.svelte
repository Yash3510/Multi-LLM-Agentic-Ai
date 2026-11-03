<script lang="ts">
  let open = $state(false);
  const theme = { light: 'a', dark: 'b' };
  function onblur() {}
  window.addEventListener('blur', onblur);
</script>

<a href="#main" class="bg-surface-1 text-ink-2 rounded-md duration-quick">{theme.dark}</a>
{#each [1, 2] as n (n)}
  <span class="scale-100 active:scale-96 grid-rows-2" style="transform: scale(0.98)">{n}</span>
{/each}
<input class="placeholder-ink-3" onblur={() => (open = !open)} />
<!-- The measured look (ADR-0037) uses palette classes, dark variants, translucency and blur. -->
<div class="bg-gray-100 text-white hover:text-violet-500 border-zinc-950/40 bg-white/60"></div>
<div class="dark:bg-gray-850 backdrop-blur-md blur-sm scale-125"></div>

<style>
  .x {
    filter: grayscale(100%);
    color: var(--color-ink-1);
    scale: 1.25;
    backdrop-filter: blur(4px);
    background: rgba(255, 255, 255, 0.7);
  }
</style>
