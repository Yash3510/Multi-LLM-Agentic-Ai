// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { arrive } from './arrive';

const settle = () => Promise.resolve();
const blocks = (count: number) => Array.from({ length: count }, (_, i) => `<p>${i}</p>`).join('');

describe('arrive', () => {
  let host: HTMLElement;
  let stop: () => void;

  beforeEach(() => {
    vi.useFakeTimers();
    host = document.createElement('div');
    host.innerHTML = blocks(1);
    document.body.append(host);
    stop = arrive(360)(host);
  });

  afterEach(() => {
    stop();
    host.remove();
    vi.useRealTimers();
  });

  it('marks only the blocks that appear after mount', async () => {
    host.innerHTML = blocks(2);
    await settle();
    expect(host.children[0].hasAttribute('data-arrive')).toBe(false);
    expect(host.children[1].hasAttribute('data-arrive')).toBe(true);
  });

  it('carries a fading block on from its age when the element is rewritten', async () => {
    host.innerHTML = blocks(2);
    await settle();
    vi.advanceTimersByTime(100);
    host.innerHTML = blocks(3);
    await settle();
    expect((host.children[1] as HTMLElement).style.animationDelay).toBe('-100ms');
    expect((host.children[2] as HTMLElement).style.animationDelay).toBe('0ms');
  });

  it('leaves a block alone once its fade has finished', async () => {
    host.innerHTML = blocks(2);
    await settle();
    vi.advanceTimersByTime(400);
    host.innerHTML = blocks(2);
    await settle();
    expect(host.children[1].hasAttribute('data-arrive')).toBe(false);
  });
});
