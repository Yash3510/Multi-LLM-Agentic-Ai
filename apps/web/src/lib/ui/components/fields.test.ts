import { fireEvent, render } from '@testing-library/svelte';
import { tick } from 'svelte';
import { describe, expect, it, vi } from 'vitest';
import Checkbox from './Checkbox.svelte';
import Combobox from './Combobox.svelte';
import FieldHarness from './FieldHarness.test.svelte';
import OnOffChoice from './OnOffChoice.svelte';
import SegmentedControl from './SegmentedControl.svelte';
import Select from './Select.svelte';
import TextInput from './TextInput.svelte';

const described = (element: Element) =>
  (element.getAttribute('aria-describedby') ?? '')
    .split(' ')
    .map((id) => document.getElementById(id)?.textContent?.trim());

describe('Field with a text input', () => {
  it('labels the input and describes it with the description', () => {
    const { getByRole } = render(FieldHarness, { kind: 'text' });
    const input = getByRole('textbox', { name: 'Ratio' });
    expect(input.getAttribute('aria-required')).toBe('true');
    expect(input.hasAttribute('aria-invalid')).toBe(false);
    expect(described(input)).toEqual(['Between 0 and 1']);
  });

  it('marks the input invalid and adds the error to its description', () => {
    const { getByRole } = render(FieldHarness, { kind: 'text', error: 'Enter a number' });
    const input = getByRole('textbox', { name: 'Ratio' });
    expect(input.getAttribute('aria-invalid')).toBe('true');
    expect(described(input)).toEqual(['Between 0 and 1', 'Enter a number']);
  });

  it('disables the input from the Field', () => {
    const { getByRole } = render(FieldHarness, { kind: 'text', disabled: true });
    expect((getByRole('textbox') as HTMLInputElement).disabled).toBe(true);
  });

  it('clears the text and keeps focus in the input', async () => {
    const { getByRole, queryByRole } = render(FieldHarness, { kind: 'text', value: 'CASE-0142' });
    await fireEvent.click(getByRole('button', { name: 'Clear' }));
    const input = getByRole('textbox') as HTMLInputElement;
    expect(input.value).toBe('');
    expect(document.activeElement).toBe(input);
    expect(queryByRole('button', { name: 'Clear' })).toBeNull();
  });
});

describe('Field as a group', () => {
  it('makes a checkbox list one group, named with "required" and described by the error', () => {
    const { getByRole } = render(FieldHarness, { kind: 'checks', error: 'Pick a rule' });
    const group = getByRole('group', { name: 'Rules Required' });
    expect(described(group)).toEqual(['Pick one or more', 'Pick a rule']);
    // Each box keeps its own name; the group's description is not repeated on every box.
    const box = getByRole('checkbox', { name: 'R2' });
    expect(box.hasAttribute('aria-describedby')).toBe(false);
  });

  it('lets a radio group take the name over, so there is one group, not two', async () => {
    const { getByRole, queryByRole } = render(FieldHarness, { kind: 'radios' });
    await tick();
    expect(queryByRole('group')).toBeNull();
    const radios = getByRole('radiogroup', { name: 'Unit' });
    expect(radios.getAttribute('aria-required')).toBe('true');
    expect(described(radios)).toEqual(['Shown beside every value']);
  });

  it('chooses an option from a press on its label text', async () => {
    const { getByRole, getByText } = render(FieldHarness, { kind: 'radios' });
    await fireEvent.click(getByText('Percent'));
    expect(getByRole('radio', { name: 'Percent' }).getAttribute('aria-checked')).toBe('true');
    expect(getByRole('radio', { name: 'Seconds' }).getAttribute('aria-checked')).toBe('false');
  });
});

describe('Checkbox', () => {
  it('reads as mixed, and becomes checked on the next press', async () => {
    const { getByRole } = render(Checkbox, { label: 'All rules', indeterminate: true });
    const box = getByRole('checkbox', { name: 'All rules' });
    expect(box.getAttribute('aria-checked')).toBe('mixed');
    await fireEvent.click(box);
    expect(box.getAttribute('aria-checked')).toBe('true');
  });

  it('ignores presses when read-only', async () => {
    const { getByRole } = render(Checkbox, { label: 'R2', checked: true, readonly: true });
    const box = getByRole('checkbox', { name: 'R2' });
    await fireEvent.click(box);
    expect(box.getAttribute('aria-checked')).toBe('true');
    expect(box.getAttribute('aria-readonly')).toBe('true');
  });

  it('keeps the description out of the name', () => {
    const { getByRole } = render(Checkbox, { label: 'R2', description: 'Ratio above limit' });
    const box = getByRole('checkbox', { name: 'R2' });
    expect(described(box)).toEqual(['Ratio above limit']);
  });
});

describe('OnOffChoice', () => {
  it('is a worded radio group, not a switch, and reports the change as a boolean', async () => {
    const changes: boolean[] = [];
    const { getByRole, queryByRole } = render(OnOffChoice, {
      'aria-label': 'Units',
      offLabel: 'Hidden',
      onLabel: 'Shown',
      onCheckedChange: (on: boolean) => changes.push(on),
    });
    expect(queryByRole('switch')).toBeNull();
    getByRole('radiogroup', { name: 'Units' });
    const hidden = getByRole('radio', { name: 'Hidden' });
    expect(hidden.getAttribute('aria-checked')).toBe('true');
    await fireEvent.click(getByRole('radio', { name: 'Shown' }));
    expect(getByRole('radio', { name: 'Shown' }).getAttribute('aria-checked')).toBe('true');
    expect(changes).toEqual([true]);
  });

  it('refuses the change when read-only', async () => {
    const changes: boolean[] = [];
    const { getByRole } = render(OnOffChoice, {
      'aria-label': 'Units',
      checked: true,
      readonly: true,
      onCheckedChange: (on: boolean) => changes.push(on),
    });
    await fireEvent.click(getByRole('radio', { name: 'Off' }));
    expect(getByRole('radio', { name: 'On' }).getAttribute('aria-checked')).toBe('true');
    expect(getByRole('radiogroup').getAttribute('aria-readonly')).toBe('true');
    expect(changes).toEqual([]);
  });
});

describe('SegmentedControl', () => {
  it('is a radio group with one tab stop, on the chosen segment', () => {
    const { getAllByRole } = render(SegmentedControl, {
      'aria-label': 'Range',
      value: 'week',
      options: [
        { value: 'day', label: 'Day' },
        { value: 'week', label: 'Week' },
      ],
    });
    const [day, week] = getAllByRole('radio');
    expect(week.getAttribute('aria-checked')).toBe('true');
    expect(week.tabIndex).toBe(0);
    expect(day.tabIndex).toBe(-1);
  });
});

describe('Combobox', () => {
  const OPTIONS = [
    { value: 'a', label: 'Ratio above limit' },
    { value: 'b', label: 'Rule R2: ratio' },
    { value: 'c', label: 'Count' },
  ];

  it('reports how many options match while typing, and when none do', async () => {
    const { getByRole } = render(Combobox, { options: OPTIONS, 'aria-label': 'Rule' });
    const input = getByRole('combobox', { name: 'Rule' }) as HTMLInputElement;
    await fireEvent.keyDown(input, { key: 'ArrowDown' });
    await fireEvent.input(input, { target: { value: 'ratio' } });
    expect(getByRole('status').textContent).toBe('2 options');
    await fireEvent.input(input, { target: { value: 'CASE-0142' } });
    expect(getByRole('status').textContent).toBe('No matches');
  });

  it('shows the chosen label, and puts it back when the list closes', async () => {
    const { getByRole } = render(Combobox, { options: OPTIONS, value: 'c', 'aria-label': 'Rule' });
    const input = getByRole('combobox') as HTMLInputElement;
    await tick();
    expect(input.value).toBe('Count');
    await fireEvent.keyDown(input, { key: 'ArrowDown' });
    await fireEvent.input(input, { target: { value: 'Cou' } });
    await fireEvent.keyDown(input, { key: 'Escape' });
    await tick();
    expect(input.value).toBe('Count');
  });
});

describe('Read-only fields', () => {
  it('copies the whole value when the shown text is shortened, and says so', async () => {
    const writeText = vi.fn(() => Promise.resolve());
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });
    const { getByRole } = render(TextInput, {
      'aria-label': 'Fingerprint',
      value: '9f2c1a7b…',
      copyValue: '9f2c1a7be04d63c8',
      sealed: true,
    });
    expect(getByRole('textbox', { name: 'Fingerprint' }).hasAttribute('readonly')).toBe(true);
    await fireEvent.click(getByRole('button', { name: 'Copy' }));
    await tick();
    expect(writeText).toHaveBeenCalledWith('9f2c1a7be04d63c8');
    expect(getByRole('status').textContent).toBe('Copied');
  });

  it('keeps a read-only Select named, and still submits its value', () => {
    const { getByRole, container } = render(Select, {
      'aria-label': 'Unit',
      name: 'unit',
      value: 'pct',
      readonly: true,
      options: [
        { value: 's', label: 'Seconds' },
        { value: 'pct', label: 'Percent' },
      ],
    });
    expect((getByRole('textbox', { name: 'Unit' }) as HTMLInputElement).value).toBe('Percent');
    const hidden = container.querySelector<HTMLInputElement>('input[type="hidden"][name="unit"]');
    expect(hidden?.value).toBe('pct');
  });
});
