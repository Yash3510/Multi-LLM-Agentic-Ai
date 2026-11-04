<script lang="ts">
  // On or off, as a worded two-option choice. There is no sliding switch: both states are words a
  // person can read, the chosen one carries the selected recipe, and it is a radio group to
  // assistive technology. Name the states for what they do ("Hidden", "Shown") where plain "Off"
  // and "On" would be vague. In lists and forms, a Checkbox is the on/off control instead.
  import type { ComponentProps } from 'svelte';
  import { fieldText } from './field-text';
  import SegmentedControl from './SegmentedControl.svelte';

  type Props = Omit<
    ComponentProps<typeof SegmentedControl>,
    'value' | 'options' | 'onValueChange' | 'fill'
  > & {
    checked?: boolean;
    offLabel?: string;
    onLabel?: string;
    onCheckedChange?: (checked: boolean) => void;
  };

  let {
    checked = $bindable(false),
    offLabel = fieldText.off(),
    onLabel = fieldText.on(),
    onCheckedChange,
    ...rest
  }: Props = $props();

  // Off first, so the order reads the same in every settings row.
  const options = $derived([
    { value: 'off', label: offLabel },
    { value: 'on', label: onLabel },
  ]);
</script>

<SegmentedControl
  {...rest}
  {options}
  bind:value={
    () => (checked ? 'on' : 'off'),
    (next) => {
      checked = next === 'on';
      onCheckedChange?.(checked);
    }
  }
/>
