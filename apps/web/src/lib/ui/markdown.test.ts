import { describe, expect, it } from 'vitest';
import { renderMarkdown } from './markdown';

const dom = (markdown: string) => {
  const box = document.createElement('div');
  box.innerHTML = renderMarkdown(markdown);
  return box;
};

describe('renderMarkdown', () => {
  it('keeps paragraphs, emphasis and lists', () => {
    const box = dom('R2 is **within** the limit.\n\n- first\n- second');
    expect(box.querySelector('p strong')?.textContent).toBe('within');
    expect(box.querySelectorAll('ul li')).toHaveLength(2);
  });

  it('renders a fenced code block with its language and the code as text', () => {
    const box = dom('```python\nprint("<b>hi</b>")\n```');
    const code = box.querySelector('pre code');
    expect(code?.className).toBe('language-python');
    expect(code?.textContent).toBe('print("<b>hi</b>")\n');
    expect(box.querySelector('pre b')).toBeNull();
  });

  it('renders a table with header and body cells', () => {
    const box = dom('| Rule | Value |\n| --- | ---: |\n| R2 | 82.5 % |');
    expect([...box.querySelectorAll('thead th')].map((cell) => cell.textContent)).toEqual([
      'Rule',
      'Value',
    ]);
    expect(box.querySelector('tbody td:last-child')?.textContent).toBe('82.5 %');
  });

  it('opens links in a new tab without handing over the opener', () => {
    const link = dom('[the report](https://example.org/report)').querySelector('a')!;
    expect(link.getAttribute('href')).toBe('https://example.org/report');
    expect(link.getAttribute('target')).toBe('_blank');
    expect(link.getAttribute('rel')).toBe('noopener noreferrer');
  });

  it('strips script, event handlers and javascript: links', () => {
    const html = renderMarkdown(
      'Hi <script>alert(1)</script><img src=x onerror="alert(2)"> [click](javascript:alert(3))',
    );
    expect(html).not.toMatch(/<script|onerror|javascript:/i);
    const box = dom('[click](javascript:alert(3))');
    expect(box.querySelector('a')?.hasAttribute('href') ?? false).toBe(false);
  });
});
