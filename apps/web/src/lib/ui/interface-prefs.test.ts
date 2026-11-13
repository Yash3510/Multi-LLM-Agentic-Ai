import { describe, expect, it } from 'vitest';
import { SECTIONS, cycle, defaults, scaleLabel } from './interface-prefs';

describe('interface preferences (common F68)', () => {
  it('has the sections in order, without the rows the owner left out', () => {
    expect(SECTIONS.map((section) => section.heading)).toEqual([
      '4CE',
      'UI',
      'Chat',
      'Input',
      'Artifacts',
      'Voice',
      'File',
    ]);
    const labels = SECTIONS.flatMap((section) => section.rows.map((row) => row.label));
    expect(labels).not.toContain('Toast Notifications for New Updates');
    expect(labels).not.toContain('Web Search in Chat');
    expect(labels).toContain('Allow User Location');
  });

  it("starts each row where the running app's capture account does", () => {
    const start = defaults();
    expect(start.trustView).toBe(true);
    expect(start.userLocation).toBe(false);
    expect(start.chatDirection).toBe('auto');
    expect(start.enterBehavior).toBe('enter');
    expect(start.uploadMode).toBe('retrieval');
  });

  it('steps a cycle button through its choices', () => {
    const row = SECTIONS.flatMap((section) => section.rows).find(
      (one) => one.key === 'chatDirection',
    )!;
    expect(cycle(row, 'auto')).toBe('ltr');
    expect(cycle(row, 'ltr')).toBe('rtl');
    expect(cycle(row, 'rtl')).toBe('auto');
  });

  it('writes a custom interface scale like 1.2x', () => {
    expect(scaleLabel(undefined)).toBe('Default');
    expect(scaleLabel(1.2)).toBe('1.2x');
  });
});
