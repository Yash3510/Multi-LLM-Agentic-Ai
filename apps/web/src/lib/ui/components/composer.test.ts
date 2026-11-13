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

describe('Composer while an answer streams', () => {
  it('offers Stop in place of send and calls onstop', async () => {
    const onstop = vi.fn();
    const { getByRole, queryByRole } = render(Composer, {
      onsend: vi.fn(),
      onstop,
      busy: true,
      model: 'Planner',
    });
    expect(queryByRole('button', { name: 'Voice mode' })).toBeNull();
    await fireEvent.click(getByRole('button', { name: 'Stop' }));
    expect(onstop).toHaveBeenCalledOnce();
  });
  it('offers a suggestion in the empty box and takes it on Tab', async () => {
    const view = render(Composer, {
      onsend: vi.fn(),
      model: 'Planner',
      tools: 7,
      suggestion: 'Check a threshold against R2 · Ratio',
    });
    const box = view.getByRole('textbox', { name: 'Message' }) as HTMLTextAreaElement;
    expect(box.placeholder).toBe('Check a threshold against R2 · Ratio');
    expect(view.getByText('Tab')).toBeTruthy();
    await fireEvent.keyDown(box, { key: 'Tab' });
    expect(box.value).toBe('Check a threshold against R2 · Ratio');
    expect(view.queryByText('Tab')).toBeNull();
  });

  it('lets Tab move focus as usual once there is text', async () => {
    const view = render(Composer, { onsend: vi.fn(), model: 'Planner', tools: 7, suggestion: 'x' });
    const box = view.getByRole('textbox', { name: 'Message' }) as HTMLTextAreaElement;
    await fireEvent.input(box, { target: { value: 'mine' } });
    const tab = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true });
    box.dispatchEvent(tab);
    expect(tab.defaultPrevented).toBe(false);
    expect(box.value).toBe('mine');
  });
});
