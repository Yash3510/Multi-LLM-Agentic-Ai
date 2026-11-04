<script lang="ts">
  // A line-1 hairline between groups. Decorative by default, so assistive technology skips it; pass
  // decorative={false} where the break is part of the structure, as between toolbar groups.
  import { Separator } from 'bits-ui';

  type Props = {
    orientation?: 'horizontal' | 'vertical';
    decorative?: boolean;
    class?: string;
  };

  let { orientation = 'horizontal', decorative = true, class: className }: Props = $props();
</script>

<Separator.Root {orientation} {decorative}>
  {#snippet child({ props })}
    <div {...props} class={['separator', className]}></div>
  {/snippet}
</Separator.Root>

<style>
  .separator {
    flex-shrink: 0;
    background-color: var(--color-hair);
  }

  .separator[data-orientation='horizontal'] {
    block-size: 1px;
    inline-size: 100%;
  }

  .separator[data-orientation='vertical'] {
    align-self: stretch;
    inline-size: 1px;
    min-block-size: var(--spacing-4);
  }
</style>
