<script lang="ts">
  // The risk notice shown before a tool is created or imported (workspace look §9.1, F112, F114):
  // a yellow box of warnings, then the acknowledgement.
</script>

<div class="risk">
  Please carefully review the following warnings:
  <ul>
    <li>Tools have a function calling feature that allows arbitrary code execution.</li>
    <li>Do not install tools from sources you do not fully trust.</li>
  </ul>
</div>
<p class="acknowledge">
  I acknowledge that I have read and I understand the implications of my action. I am aware of the
  risks associated with executing arbitrary code and I have verified the trustworthiness of the
  source.
</p>

<style>
  /* The risk notice (look §9.1): a yellow box of warnings, then the acknowledgement. */
  .risk {
    margin-block-start: 8px;
    padding: 12px 16px;
    border-radius: 8px;
    background-color: color-mix(in srgb, var(--color-yellow-500) 20%, transparent);
    color: var(--color-yellow-700);
    font-size: var(--text-ui);
    line-height: 20px;
  }

  :global([data-theme='dark']) .risk {
    color: var(--color-yellow-200);
  }

  .risk ul {
    margin-block-start: 4px;
    padding-inline-start: 16px;
    font-size: var(--text-caption);
    line-height: 16px;
    list-style: disc;
  }

  .acknowledge {
    margin-block: 12px;
    color: var(--color-gray-500);
    font-size: var(--text-ui);
    line-height: 20px;
  }
</style>
