/** Copy feedback holds this long (design-system.md, "Motion"). */
export const COPY_HOLD_MS = 1600;

// Without a secure context (an appliance on plain http) there is no Clipboard API, so fall back to
// the older copy command on an off-screen field, then give focus back to whoever had it.
function legacyCopy(text: string): boolean {
  const focused = document.activeElement as HTMLElement | null;
  const field = document.createElement('textarea');
  field.value = text;
  field.setAttribute('readonly', '');
  field.setAttribute('aria-hidden', 'true');
  field.style.position = 'fixed';
  field.style.insetBlockStart = '0';
  field.style.opacity = '0';
  document.body.append(field);
  field.focus({ preventScroll: true });
  field.select();
  try {
    return document.execCommand('copy');
  } catch {
    return false;
  } finally {
    field.remove();
    focused?.focus({ preventScroll: true });
  }
}

/** Puts text on the clipboard; false when the browser refuses both ways. */
export async function writeClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return legacyCopy(text);
  }
}
