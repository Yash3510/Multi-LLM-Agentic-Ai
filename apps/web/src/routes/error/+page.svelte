<script lang="ts">
  // The backend-required page (entry look E3): shown when the app is served without the 4CE
  // backend. Check Again reloads from the start, which tries the backend again.
  import { m } from '$lib/i18n/generated/messages.js';
</script>

<svelte:head><title>{m.app_name()}</title></svelte:head>

<div class="layer">
  <div class="panel">
    <div class="content">
      <div class="text">
        <h1>{m.backend_required_title({ name: m.app_name() })}</h1>
        <p>{m.backend_required_body({ name: m.app_name() })}</p>
      </div>
      <button type="button" onclick={() => location.assign('/')}>{m.backend_check_again()}</button>
    </div>
  </div>
</div>

<style>
  .layer {
    position: absolute;
    inset: 0;
    z-index: 50;
    display: flex;
  }

  .panel {
    position: absolute;
    inset: 0;
    display: flex;
    justify-content: center;
    border-radius: 12px;
    backdrop-filter: blur(4px);
  }

  .content {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin: auto;
    padding-block-end: 176px;
  }

  .text {
    max-inline-size: 448px;
    text-align: center;
  }

  h1 {
    font-size: 24px;
    font-weight: 400;
    line-height: 32px;
  }

  p {
    inline-size: 100%;
    margin-block-start: var(--spacing-4);
    font-size: 14px;
    line-height: 20px;
  }

  button {
    position: relative;
    z-index: 20;
    margin-block-start: var(--spacing-6);
    padding: var(--spacing-2) 20px;
    border-radius: var(--radius-pill);
    background-color: var(--color-gray-100);
    color: var(--color-black);
    font-size: 14px;
    transition: background-color 150ms;
  }

  button:hover {
    background-color: var(--color-gray-200);
  }

  button:focus-visible {
    outline: none;
    box-shadow: var(--shadow-focus);
  }
</style>
