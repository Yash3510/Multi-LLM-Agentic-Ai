// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest';
import { glide } from './glide';

/** jsdom has no layout, so each row is given the box the browser would report. */
function row(top: number, current = false) {
  const el = document.createElement('button');
  el.className = 'row';
  if (current) el.setAttribute('aria-current', 'page');
  Object.defineProperties(el, {
    offsetLeft: { value: 4 },
    offsetTop: { value: top },
    offsetWidth: { value: 120 },
    offsetHeight: { value: 28 },
  });
  return el;
}

function host(...rows: HTMLElement[]) {
  const el = document.createElement('div');
  el.append(...rows);
  document.body.append(el);
  return el;
}

const marker = (el: HTMLElement, kind: string) =>
  el.querySelector<HTMLElement>(`[data-glide='${kind}']`)!;
const flush = () => new Promise((resolve) => setTimeout(resolve));

afterEach(() => document.body.replaceChildren());

describe('glide', () => {
  it('lays a hidden-from-readers marker over the active row', () => {
    const el = host(row(0), row(32, true));
    glide({ active: '.row[aria-current]' })(el);
    const pill = marker(el, 'active');
    expect(pill.getAttribute('aria-hidden')).toBe('true');
    expect(pill.dataset.on).toBe('');
    expect(pill.style.getPropertyValue('--glide-y')).toBe('32px');
    expect(pill.style.getPropertyValue('--glide-x')).toBe('4px');
    expect(pill.style.getPropertyValue('--glide-w')).toBe('120px');
    expect(pill.style.getPropertyValue('--glide-h')).toBe('28px');
  });

  it('follows the active row when it changes, and hides when none is active', async () => {
    const [first, second] = [row(0, true), row(32)];
    const el = host(first, second);
    glide({ active: '.row[aria-current]' })(el);
    first.removeAttribute('aria-current');
    second.setAttribute('aria-current', 'page');
    await flush();
    expect(marker(el, 'active').style.getPropertyValue('--glide-y')).toBe('32px');
    second.removeAttribute('aria-current');
    await flush();
    expect(marker(el, 'active').dataset.on).toBeUndefined();
  });

  it('moves the hover marker under the pointer and hides it on leave', () => {
    const second = row(32);
    const el = host(row(0), second);
    glide({ hover: '.row' })(el);
    const ghost = marker(el, 'hover');
    expect(ghost.dataset.on).toBeUndefined();
    second.dispatchEvent(new Event('pointerover', { bubbles: true }));
    expect(ghost.dataset.on).toBe('');
    expect(ghost.style.getPropertyValue('--glide-y')).toBe('32px');
    el.dispatchEvent(new Event('pointerleave'));
    expect(ghost.dataset.on).toBeUndefined();
  });

  it('leaves nothing behind when detached', () => {
    const el = host(row(0, true));
    const detach = glide({ active: '.row[aria-current]', hover: '.row' })(el);
    expect(el.dataset.glideHost).toBe('');
    detach();
    expect(el.querySelector('[data-glide]')).toBeNull();
    expect(el.dataset.glideHost).toBeUndefined();
  });
});
