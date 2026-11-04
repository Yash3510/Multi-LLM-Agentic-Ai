<script lang="ts">
  // The 24 px icon buttons at the end of a field box: clear, copy, show options. Icon-only, so the
  // label is both the accessible name and a hint that opens on hover and on keyboard focus. Other
  // props (a bits-ui trigger's, say) pass through to the button, merged with the hint's.
  import { Tooltip } from 'bits-ui';
  import type { HTMLButtonAttributes } from 'svelte/elements';
  import type { IconName } from '../icons/generated/icons';
  import Icon from '../icons/Icon.svelte';
  import { DURATION } from '../motion.svelte';
  import './field-control.css';

  type Props = Omit<HTMLButtonAttributes, 'children' | 'aria-label'> & {
    icon: IconName;
    /** The accessible name, and the hint unless `hint` says something else for a moment. */
    label: string;
    /** Shown in place of the label, e.g. "Copied" while the copy tick holds. */
    hint?: string;
  };

  let { icon, label, hint, ...rest }: Props = $props();
</script>

<Tooltip.Provider delayDuration={DURATION.slow}>
  <Tooltip.Root>
    <Tooltip.Trigger {...rest as Tooltip.TriggerProps}>
      {#snippet child({ props })}
        <!-- The hint repeats the name, so it is not also the button's description. -->
        <button
          {...props}
          type="button"
          class="field-control-button"
          aria-label={label}
          aria-describedby={rest['aria-describedby']}
        >
          <Icon name={icon} size={16} />
        </button>
      {/snippet}
    </Tooltip.Trigger>
    <Tooltip.Portal>
      <Tooltip.Content class="field-hint" sideOffset={6} collisionPadding={8}>
        {hint ?? label}
      </Tooltip.Content>
    </Tooltip.Portal>
  </Tooltip.Root>
</Tooltip.Provider>
