import { render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import FileCard from './FileCard.svelte';

const file = {
  name: 'CASE-0142 answer.docx',
  kind: 'docx',
  size: 18_874,
  hash: '9c2e5b8f1a4d7c0e3b6f9a2d5c8e1b4f',
  classification: 'Internal',
  state: 'ready' as const,
};

describe('FileCard', () => {
  it('shows the type, name, size, hash prefix and classification of a ready file', () => {
    const { container, getByText } = render(FileCard, { props: { file } });
    expect(getByText('CASE-0142 answer.docx')).toBeTruthy();
    const text = container.textContent?.replace(/\s+/g, ' ');
    for (const part of ['DOCX', '18.4 KB', '9c2e5b8f…', 'Internal']) expect(text).toContain(part);
    expect(text).not.toContain('Scanning');
  });

  it('says the state of a file that is not ready yet', () => {
    const { container } = render(FileCard, { props: { file: { ...file, state: 'scanning' } } });
    expect(container.textContent).toContain('Scanning');
  });
});
