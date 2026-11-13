<script lang="ts">
  // A password field with show and hide (admin look S8, plain variant). The value is never
  // logged or kept beyond the form that owns it.
  import Icon from '$lib/ui/icons/Icon.svelte';

  type Props = {
    value: string;
    label: string;
    placeholder?: string;
    autocomplete?: 'new-password' | 'current-password' | 'off';
    required?: boolean;
  };

  let { value = $bindable(), label, placeholder, autocomplete = 'off', required }: Props = $props();

  let shown = $state(false);
</script>

<span class="secret">
  <input
    class="plain"
    type={shown ? 'text' : 'password'}
    bind:value
    aria-label={label}
    {placeholder}
    {autocomplete}
    {required}
  />
  <button
    type="button"
    aria-label={shown ? 'Hide password' : 'Show password'}
    onclick={() => (shown = !shown)}><Icon name={shown ? 'eye-slash' : 'eye'} size={16} /></button
  >
</span>
