import { afterEach, describe, expect, it, vi } from 'vitest';
import { writeClipboard } from './clipboard';

describe('writeClipboard', () => {
  afterEach(() => {
    Reflect.deleteProperty(navigator, 'clipboard');
    Reflect.deleteProperty(document, 'execCommand');
  });

  it('uses the Clipboard API when there is one', async () => {
    const writeText = vi.fn(() => Promise.resolve());
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });
    expect(await writeClipboard('CASE-0142')).toBe(true);
    expect(writeText).toHaveBeenCalledWith('CASE-0142');
  });

  it('falls back to the copy command without one, and gives focus back', async () => {
    const button = document.body.appendChild(document.createElement('button'));
    button.focus();
    let copied = '';
    Object.defineProperty(document, 'execCommand', {
      configurable: true,
      value: () => {
        const field = document.activeElement as HTMLTextAreaElement;
        copied = field.value.slice(field.selectionStart, field.selectionEnd);
        return true;
      },
    });
    expect(await writeClipboard('3f9a21c0')).toBe(true);
    expect(copied).toBe('3f9a21c0');
    expect(document.activeElement).toBe(button);
    expect(document.querySelector('textarea')).toBeNull();
    button.remove();
  });

  it('says false when the browser refuses both ways', async () => {
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: () => Promise.reject(new Error('denied')) },
      configurable: true,
    });
    Object.defineProperty(document, 'execCommand', { configurable: true, value: () => false });
    expect(await writeClipboard('R2')).toBe(false);
  });
});
