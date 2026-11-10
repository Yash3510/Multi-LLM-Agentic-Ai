import { describe, expect, it } from 'vitest';
import { ADMIN_GROUPS, PANELS, panelDefaults, shownItems } from './admin-panels';

describe('admin settings panels (admin look §18 to §32)', () => {
  it('lists the admin tabs under their groups, without Web Search', () => {
    expect(ADMIN_GROUPS.map((group) => group.caption)).toEqual([
      'System',
      'AI',
      'Experience',
      'Quality',
      'Tools',
      'Data',
    ]);
    const labels = ADMIN_GROUPS.flatMap((group) => group.tabs.map((tab) => tab.label));
    expect(labels).toContain('Authentication');
    expect(labels).not.toContain('Web Search');
  });

  it('starts each panel from its defaults', () => {
    expect(panelDefaults(PANELS.general)).toMatchObject({
      ENABLE_MESSAGE_RATING: true,
      ENABLE_CHANNELS: false,
    });
    expect(panelDefaults(PANELS.authentication)).toMatchObject({
      DEFAULT_USER_ROLE: 'pending',
      JWT_EXPIRES_IN: '4w',
    });
  });

  it('shows sub-settings only while their parent is on', () => {
    const general = PANELS.general;
    const values = panelDefaults(general);
    const labels = (v: Record<string, unknown>) =>
      general.sections.flatMap((section) => shownItems(section, v).map((item) => item.label));
    expect(labels(values)).toContain('Folder Max File Count');
    expect(labels({ ...values, ENABLE_FOLDERS: false })).not.toContain('Folder Max File Count');
    expect(labels(values)).not.toContain('Model Response Mode');
  });

  it('keeps LDAP and OAuth as locked look-only rows', () => {
    const auth = PANELS.authentication;
    const locked = auth.sections.flatMap((section) => section.items).filter((item) => item.locked);
    expect(locked.map((item) => item.label)).toEqual(['LDAP', 'OAuth / OIDC']);
  });
});

describe('admin panels kept local (owner rule)', () => {
  it('offers only local or self-hosted engines', () => {
    const options = (panel: keyof typeof PANELS, key: string) =>
      PANELS[panel].sections
        .flatMap((section) => section.items)
        .find((item) => item.key === key)
        ?.options?.map(([value]) => value);
    expect(options('audio', 'STT_ENGINE')).toEqual(['']);
    expect(options('audio', 'TTS_ENGINE')).toEqual(['', 'transformers']);
    expect(options('images', 'IMAGE_GENERATION_ENGINE')).toEqual(['comfyui', 'automatic1111']);
    expect(options('documents', 'RAG_EMBEDDING_ENGINE')).toEqual(['', 'ollama']);
    expect(options('documents', 'CONTENT_EXTRACTION_ENGINE')).toEqual([
      '',
      'tika',
      'docling',
      'mineru',
    ]);
  });
});
