import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { playIntro } from './intro';

// The intro reads its ink and ground from the tokens; jsdom loads no stylesheet, so the test
// sets them (as rgb, which the browser hands back for the same tokens in a computed style).
const root = document.documentElement;
const overlay = () => document.getElementById('fource-intro');
const run = (ms: number) => {
  for (let t = 0; t < ms; t += 16) vi.advanceTimersByTime(16);
};

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['requestAnimationFrame', 'cancelAnimationFrame', 'performance'] });
  root.style.setProperty('--color-intro-ink', 'rgb(13, 17, 23)');
  root.style.setProperty('--color-intro-ground', 'rgb(255, 255, 255)');
  document.body.innerHTML = '';
});

afterEach(() => {
  run(8000);
  vi.useRealTimers();
  delete root.dataset.motion;
});

describe('intro (entry look E4)', () => {
  it('covers the screen once, however often it is asked to play', () => {
    playIntro();
    playIntro();
    expect(document.querySelectorAll('#fource-intro')).toHaveLength(1);
    expect(overlay()?.getAttribute('aria-hidden')).toBe('true');
    expect(overlay()?.style.zIndex).toBe('2147483000');
  });

  // A minifier may shorten a token's value, or name it; any colour the browser reads will do.
  it('reads its colours however the tokens are written', () => {
    root.style.setProperty('--color-intro-ground', 'white');
    playIntro();
    expect(overlay()?.style.background).toBe('rgb(255, 255, 255)');
  });

  it('draws the brand-kit mark', () => {
    playIntro();
    const mark = overlay()?.querySelector('#fi-mk')?.getAttribute('d') ?? '';
    expect(mark.startsWith('M138.66,0.00 134.79,1.44')).toBe(true);
  });

  it('plays through and leaves with no logo to land on', () => {
    playIntro();
    run(5000);
    expect(overlay()).not.toBeNull();
    run(1000);
    expect(overlay()).toBeNull();
  });

  it('skips to the ending on a key press', () => {
    playIntro();
    run(300);
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    run(2700);
    expect(overlay()).toBeNull();
  });

  it('shows a still mark and a fade under reduced motion', () => {
    root.dataset.motion = 'reduce';
    playIntro();
    const svg = overlay()?.querySelector('svg');
    const whole = svg?.querySelector<SVGElement>('use[href="#fi-mk"]:not([clip-path])');
    expect(whole?.style.display).toBe('');
    run(1900);
    expect(overlay()).toBeNull();
  });

  it('glides onto the sidebar logo and hides it until it lands', () => {
    document.body.innerHTML = '<span data-intro-logo><img alt="" /></span>';
    const logo = document.querySelector('img')!;
    logo.getBoundingClientRect = () =>
      ({ left: 20, top: 20, width: 22, height: 22, right: 42, bottom: 42 }) as DOMRect;
    playIntro();
    run(4000);
    expect(logo.style.visibility).toBe('hidden');
    run(1100);
    expect(logo.style.visibility).toBe('');
    expect(overlay()).not.toBeNull();
    run(800);
    expect(overlay()).toBeNull();
  });
});
