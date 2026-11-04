<script lang="ts">
  // The 4CE logomark, from the owner's brand kit and used as shipped: the ink file on light
  // grounds, the white file on dark. Decorative; the link or button around it carries the name.
  import ink from '$lib/ui/brand/4ce-logomark-ink.svg';
  import white from '$lib/ui/brand/4ce-logomark-white.svg';

  let { size = 22 }: { size?: number } = $props();
</script>

<span class="mark">
  <img src={ink} alt="" width={size} height={size} data-theme="light" />
  <img src={white} alt="" width={size} height={size} data-theme="dark" />
</span>

<style>
  .mark {
    display: inline-grid;
    flex-shrink: 0;
  }

  img {
    grid-area: 1 / 1;
    max-inline-size: none;
  }

  img[data-theme='dark'],
  :global([data-theme='dark']) img[data-theme='light'] {
    display: none;
  }

  :global([data-theme='dark']) img[data-theme='dark'] {
    display: block;
  }
</style>
