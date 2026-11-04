import { fireEvent, render } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import Composer from './Composer.svelte';

const setup = () => {
  const onsend = vi.fn();
  const view = render(Composer, { onsend, model: 'Planner', tools: 7 });
  const box = view.getByRole('textbox', { name: 'Message' }) as HTMLTextAreaElement;
  return { ...view, onsend, box };
};

describe('Composer', () => {
  it('offers voice mode when empty and send once there is text', async () => {
    const { getByRole, box } = setup();
    expect(getByRole('button', { name: 'Voice mode' })).toBeTruthy();
    await fireEvent.input(box, { target: { value: 'Is R2 within the limit?' } });
    expect(getByRole('button', { name: 'Send' })).toBeTruthy();
  });

  it('sends the trimmed text on Enter and clears the box; Shift+Enter keeps writing', async () => {
    const { box, onsend } = setup();
    await fireEvent.input(box, { target: { value: '  Check CASE-0142  ' } });
    await fireEvent.keyDown(box, { key: 'Enter', shiftKey: true });
    expect(onsend).not.toHaveBeenCalled();
    await fireEvent.keyDown(box, { key: 'Enter' });
    expect(onsend).toHaveBeenCalledWith('Check CASE-0142');
    expect(box.value).toBe('');
  });

  it('never sends blank text or while an input method is composing', async () => {
    const { box, onsend } = setup();
    await fireEvent.input(box, { target: { value: '   ' } });
    await fireEvent.keyDown(box, { key: 'Enter' });
    await fireEvent.input(box, { target: { value: 'नमस्ते' } });
    await fireEvent.keyDown(box, { key: 'Enter', isComposing: true });
    expect(onsend).not.toHaveBeenCalled();
  });

  it('names the tools count for assistive technology', () => {
    const { getByRole } = setup();
    expect(getByRole('button', { name: '7 Available Tools' })).toBeTruthy();
  });
});
