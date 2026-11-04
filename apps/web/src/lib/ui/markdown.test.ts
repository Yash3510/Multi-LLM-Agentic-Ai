import { describe, expect, it } from 'vitest';
import { renderMarkdown, safeHtml } from './markdown';

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

describe('safeHtml', () => {
  it('writes only what renderMarkdown produced', () => {
    const node = document.createElement('div');
    safeHtml(renderMarkdown('**ok** <script>x()</script>'))(node);
    expect(node.innerHTML).toBe('<p><strong>ok</strong> </p>\n');
  });
});

describe('citations', () => {
  const sources = [
    { index: 1, title: 'Rule R2 · Ratio', passage: '' },
    { index: 2, title: 'CASE-0142 second batch report for the plant', passage: '' },
  ];

  it('turns [n] into an evidence chip named for its source', () => {
    const box = document.createElement('div');
    box.innerHTML = renderMarkdown('Within the limit [1], per the report [2].', sources);
    const chips = [...box.querySelectorAll('cite')];
    expect(chips.map((chip) => chip.dataset.source)).toEqual(['1', '2']);
    expect(chips[0].textContent).toBe('Rule R2 · Ratio');
    expect(chips[1].textContent).toBe('CASE-0142 secon... the plant');
    expect(chips[1].getAttribute('title')).toBe(
      'View source: CASE-0142 second batch report for the plant',
    );
  });

  it('leaves [n] alone inside code and when no such source exists', () => {
    const box = document.createElement('div');
    box.innerHTML = renderMarkdown('`a[1]` and [9]', sources);
    expect(box.querySelector('cite')).toBeNull();
    expect(box.textContent).toContain('a[1]');
    expect(box.textContent).toContain('[9]');
  });
});
