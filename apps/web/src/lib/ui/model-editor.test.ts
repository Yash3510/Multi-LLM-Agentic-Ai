import { describe, expect, it } from 'vitest';
import {
  blankDraft,
  defaultFeatureChoices,
  matching,
  modelId,
  payload,
  shownCapabilities,
  validate,
} from './model-editor';

describe('model id from the name (workspace F35)', () => {
  it('lowercases, turns spaces into hyphens and drops everything else', () => {
    expect(modelId('Ratio Helper 2!')).toBe('ratio-helper-2');
    expect(modelId('  Ünit – Test  ')).toBe('-nit--test-');
  });
});

describe('saving (F51)', () => {
  it('checks the id, then the name, then the base model', () => {
    const draft = blankDraft();
    expect(validate(draft)).toBe('Model ID is required.');
    draft.id = 'x';
    expect(validate(draft)).toBe('Model Name is required.');
    draft.name = 'X';
    expect(validate(draft)).toBe('Base Model is required.');
    draft.base = 'qwen/qwen3-1.7b';
    expect(validate(draft)).toBeUndefined();
  });

  it('leaves out what is empty or at its default', () => {
    const draft = { ...blankDraft(), id: 'x', name: 'X', base: 'b', system: '   ' };
    draft.description = { custom: true, text: '  ' };
    const saved = payload(draft, 'create');
    expect(saved.params).toEqual({});
    expect(saved.meta.description).toBeNull();
    expect('builtinTools' in saved.meta).toBe(false);
    expect('defaultFeatures' in saved.meta).toBe(false);
    expect('suggestionPrompts' in saved.meta).toBe(false);
  });

  it('stores only the builtin tools that are switched off', () => {
    const draft = { ...blankDraft(), id: 'x', name: 'X', base: 'b' };
    draft.builtinTools.notes = false;
    expect(payload(draft, 'create').meta.builtinTools).toEqual({ notes: false });
  });

  it('keeps default features only for capabilities that are on', () => {
    const draft = { ...blankDraft(), id: 'x', name: 'X', base: 'b' };
    draft.defaultFeatures = ['web_search', 'code_interpreter'];
    draft.capabilities.web_search = false;
    expect(payload(draft, 'create').meta.defaultFeatures).toEqual(['code_interpreter']);
  });

  it('drops suggestion prompts with no content when creating', () => {
    const draft = { ...blankDraft(), id: 'x', name: 'X', base: 'b' };
    draft.suggestions = [
      { title: ['Hi', ''], content: '' },
      { title: ['Check', 'a limit'], content: 'Check the limit' },
    ];
    expect(payload(draft, 'create').meta.suggestionPrompts).toEqual([
      { title: ['Check', 'a limit'], content: 'Check the limit' },
    ]);
  });
});

describe('what the form shows (F46 to F48)', () => {
  it('hides File Context while File Upload is off', () => {
    const draft = blankDraft();
    expect(shownCapabilities(draft.capabilities)).toContain('file_context');
    draft.capabilities.file_upload = false;
    expect(shownCapabilities(draft.capabilities)).not.toContain('file_context');
  });

  it('offers default features only for the capabilities that are on', () => {
    const draft = blankDraft();
    draft.capabilities.image_generation = false;
    expect(defaultFeatureChoices(draft.capabilities)).toEqual(['web_search', 'code_interpreter']);
  });
});

describe('type-ahead search (F54)', () => {
  const items = [
    { id: 'limit-check', name: '4CE Threshold Check', description: 'Limits' },
    { id: 'calc', name: '4CE Engineering Calculations' },
  ];
  it('matches id, name or description, ignoring case', () => {
    expect(matching(items, 'LIMITS').map((item) => item.id)).toEqual(['limit-check']);
    expect(matching(items, 'calc').map((item) => item.id)).toEqual(['calc']);
    expect(matching(items, '')).toHaveLength(2);
  });
});
