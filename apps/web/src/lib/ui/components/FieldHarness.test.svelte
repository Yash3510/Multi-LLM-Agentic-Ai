<script lang="ts">
  // Test-only: a Field with each kind of control inside, so fields.test.ts can check the wiring.
  import Checkbox from './Checkbox.svelte';
  import Field from './Field.svelte';
  import RadioGroup from './RadioGroup.svelte';
  import TextInput from './TextInput.svelte';

  type Props = {
    kind: 'text' | 'checks' | 'radios';
    error?: string;
    disabled?: boolean;
    value?: string;
  };

  let { kind, error, disabled = false, value = $bindable('') }: Props = $props();

  const OPTIONS = [
    { value: 's', label: 'Seconds' },
    { value: 'pct', label: 'Percent' },
  ];
</script>

{#if kind === 'text'}
  <Field label="Ratio" description="Between 0 and 1" {error} {disabled} required>
    <TextInput bind:value clearable />
  </Field>
{:else if kind === 'checks'}
  <Field label="Rules" description="Pick one or more" {error} {disabled} required group>
    <Checkbox label="R2" />
    <Checkbox label="R3" />
  </Field>
{:else}
  <Field label="Unit" description="Shown beside every value" {error} required group>
    <RadioGroup bind:value options={OPTIONS} />
  </Field>
{/if}
