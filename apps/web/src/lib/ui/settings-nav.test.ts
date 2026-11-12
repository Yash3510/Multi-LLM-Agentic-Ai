import { describe, expect, it } from 'vitest';
import { scopeOf, shownGroups } from './settings-nav';

const personal = [
  { caption: 'Basics', tabs: [{ id: 'general', label: 'General' }] },
  { caption: 'Data', tabs: [{ id: 'audio', label: 'Audio' }] },
];
const admin = [
  { caption: 'System', tabs: [{ id: 'admin-general', label: 'General' }] },
  { caption: 'Experience', tabs: [{ id: 'admin-audio', label: 'Audio' }] },
];
const ids = (groups: typeof personal) => groups.flatMap((group) => group.tabs.map((one) => one.id));

describe('settings navigation', () => {
  it('shows one side at a time when nothing is searched', () => {
    expect(ids(shownGroups(personal, admin, 'personal', '', true))).toEqual(['general', 'audio']);
    expect(ids(shownGroups(personal, admin, 'admin', ' ', true))).toEqual([
      'admin-general',
      'admin-audio',
    ]);
  });

  it('never shows the admin side to someone who is not an admin', () => {
    expect(ids(shownGroups(personal, admin, 'admin', '', false))).toEqual(['general', 'audio']);
    expect(ids(shownGroups(personal, admin, 'personal', 'aud', false))).toEqual(['audio']);
  });

  it('searches both sides for an admin and drops empty groups', () => {
    const found = shownGroups(personal, admin, 'personal', ' AUD ', true);
    expect(ids(found)).toEqual(['audio', 'admin-audio']);
    expect(found.map((group) => group.caption)).toEqual(['Data', 'Experience']);
  });

  it('knows which side a tab is on', () => {
    expect(scopeOf('general')).toBe('personal');
    expect(scopeOf('admin-models')).toBe('admin');
  });
});
