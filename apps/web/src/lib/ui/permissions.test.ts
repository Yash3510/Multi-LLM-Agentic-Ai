import { describe, expect, it } from 'vitest';
import {
  DEFAULT_PERMISSIONS,
  SECTIONS,
  fillPermissions,
  hasCustom,
  visibleRows,
} from './permissions';

describe('group permissions (admin F74 to F82)', () => {
  it('fills missing keys from the built-in defaults, per category', () => {
    const filled = fillPermissions({ chat: { edit: false } });
    expect(filled.chat.edit).toBe(false);
    expect(filled.chat.share).toBe(true);
    expect(filled.workspace.models).toBe(false);
    expect(filled.access_grants.allow_users).toBe(true);
  });

  it('lists the six headings in order', () => {
    expect(SECTIONS.map((section) => section.heading)).toEqual([
      'Workspace Permissions',
      'Sharing Permissions',
      'Access Grants',
      'Chat Permissions',
      'Features Permissions',
      'Settings Permissions',
    ]);
  });

  it('shows a public sharing row only while its base row is on, and chat sharing rows only while chat share is on', () => {
    const sharing = SECTIONS[1];
    const off = visibleRows(sharing, fillPermissions({})).map((row) => row.label);
    expect(off).not.toContain('Models Public Sharing');
    expect(off).toContain('Chats Public Sharing');
    expect(off).toContain('Calendars Public Sharing');
    const on = visibleRows(
      sharing,
      fillPermissions({ sharing: { models: true }, chat: { share: false } }),
    ).map((row) => row.label);
    expect(on).toContain('Models Public Sharing');
    expect(on).not.toContain('Chats Public Sharing');
  });

  it('knows when a group stores custom permissions', () => {
    expect(hasCustom({})).toBe(false);
    expect(hasCustom({ chat: { edit: false } })).toBe(true);
  });

  it('keeps defaults as the running app ships them', () => {
    expect(DEFAULT_PERMISSIONS.features.api_keys).toBe(false);
    expect(DEFAULT_PERMISSIONS.chat.temporary_enforced).toBe(false);
  });
});
