import { fireEvent, render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import EvidenceViewer from './EvidenceViewer.svelte';

const box = { x: 0.3, y: 0.2, width: 0.25, height: 0.05 };
const evidence = {
  id: 'ev-1',
  name: 'CASE-0142 second batch report',
  kind: 'Batch report',
  pages: [{ image: 'data:image/svg+xml,%3Csvg%2F%3E', width: 600, height: 800 }],
  reader: 'qwen/qwen3-8b',
  observations: [
    { id: 'ob-1', index: 1, page: 1, box, label: 'Batch', value: 'Second', confidence: 1 },
    {
      id: 'ob-2',
      index: 2,
      page: 1,
      box,
      label: 'Ratio',
      value: '82.5',
      unit: '%',
      confidence: 0.86,
    },
  ],
};

const twoPages = {
  ...evidence,
  pages: [...evidence.pages, ...evidence.pages],
  observations: [
    ...evidence.observations,
    {
      id: 'ob-3',
      index: 3,
      page: 2,
      box,
      label: 'Temperature',
      value: '21',
      unit: '°C',
      confidence: 0.74,
    },
  ],
};

describe('EvidenceViewer', () => {
  it('moves between pages, the list following the page shown', async () => {
    const { getByRole, getByText, queryByRole } = render(EvidenceViewer, {
      props: { evidence: twoPages },
    });
    expect(getByText('Page 1 of 2')).toBeTruthy();
    expect(getByRole('button', { name: 'Previous page' }).hasAttribute('disabled')).toBe(true);
    await fireEvent.click(getByRole('button', { name: 'Next page' }));
    expect(getByRole('img', { name: `Page 2 of ${evidence.name}` })).toBeTruthy();
    expect(getByRole('button', { name: /^3 Temperature/ })).toBeTruthy();
    expect(queryByRole('button', { name: /^1 Batch/ })).toBeNull();
    expect(getByRole('button', { name: 'Next page' }).hasAttribute('disabled')).toBe(true);
  });

  it('opens on the page asked for, or on the page of the box asked for', () => {
    const byPage = render(EvidenceViewer, { props: { evidence: twoPages, page: 2 } });
    expect(byPage.getByRole('img', { name: `Page 2 of ${evidence.name}` })).toBeTruthy();
    byPage.unmount();
    const byBox = render(EvidenceViewer, { props: { evidence: twoPages, page: 1, box: 3 } });
    expect(
      byBox.getByRole('button', { name: 'Box 3: Temperature, 21 °C' }).getAttribute('aria-pressed'),
    ).toBe('true');
    byBox.unmount();
    const outside = render(EvidenceViewer, { props: { evidence: twoPages, page: 7 } });
    expect(outside.getByRole('img', { name: `Page 1 of ${evidence.name}` })).toBeTruthy();
  });

  it('zooms from the page fitting to four times its size, and back', async () => {
    const { getByRole, getByText } = render(EvidenceViewer, { props: { evidence } });
    const zoomIn = getByRole('button', { name: 'Zoom in' });
    const zoomOut = getByRole('button', { name: 'Zoom out' });
    const page = getByRole('img').parentElement;
    expect(getByText('Zoom 100%')).toBeTruthy();
    expect(zoomOut.hasAttribute('disabled')).toBe(true);
    await fireEvent.click(zoomIn);
    expect(getByText('Zoom 150%')).toBeTruthy();
    expect(page?.style.inlineSize).toBe('150%');
    for (let step = 0; step < 3; step += 1) await fireEvent.click(zoomIn);
    expect(getByText('Zoom 400%')).toBeTruthy();
    expect(zoomIn.hasAttribute('disabled')).toBe(true);
    await fireEvent.click(zoomOut);
    expect(getByText('Zoom 300%')).toBeTruthy();
  });

  it('makes the page a focusable region named for its page and zoom, so it pans with no boxes', async () => {
    const nothingRead = { ...twoPages, observations: [] };
    const { getByRole } = render(EvidenceViewer, { props: { evidence: nothingRead, page: 2 } });
    await fireEvent.click(getByRole('button', { name: 'Zoom in' }));
    const region = getByRole('region', { name: 'Page 2 of 2, zoom 150%' });
    region.focus();
    expect(document.activeElement).toBe(region);
  });

  it('shows no page controls for evidence with one page', () => {
    const { queryByRole } = render(EvidenceViewer, { props: { evidence } });
    expect(queryByRole('button', { name: 'Next page' })).toBeNull();
  });

  it('keeps the selected box and its row in step, either way', async () => {
    const { getByRole } = render(EvidenceViewer, { props: { evidence } });
    const box2 = getByRole('button', { name: 'Box 2: Ratio, 82.5 %' });
    const row1 = getByRole('button', { name: /^1 Batch/ });
    await fireEvent.click(box2);
    expect(getByRole('button', { name: /^2 Ratio/ }).getAttribute('aria-pressed')).toBe('true');
    await fireEvent.click(row1);
    expect(getByRole('button', { name: 'Box 1: Batch, Second' }).getAttribute('aria-pressed')).toBe(
      'true',
    );
    expect(box2.getAttribute('aria-pressed')).toBe('false');
  });

  it('asks for a check on what was read with less than full confidence, and opens on a box', () => {
    const { getByRole } = render(EvidenceViewer, { props: { evidence, box: 2 } });
    expect(getByRole('button', { name: /^2 Ratio/ }).textContent).toContain('check');
    expect(getByRole('button', { name: /^1 Batch/ }).textContent).not.toContain('check');
    expect(getByRole('button', { name: 'Box 2: Ratio, 82.5 %' }).getAttribute('aria-pressed')).toBe(
      'true',
    );
  });
});
