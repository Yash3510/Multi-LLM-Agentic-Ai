import { DURATION } from './motion.svelte';

/**
 * Marks the blocks that appear in an element after it mounts (a Svelte attachment), so an answer
 * fades in block by block as it is written. The element is rewritten whole on every chunk, so a
 * block that is still fading is marked again with its age as a negative delay and carries on from
 * where it was. Blocks already there at mount, such as a saved answer, are left alone.
 */
export function arrive(duration: number = DURATION.calm) {
  return (host: HTMLElement) => {
    const settled = host.children.length;
    const born: number[] = [];
    const mark = () => {
      const now = performance.now();
      for (let i = settled; i < host.children.length; i++) {
        const block = host.children[i];
        born[i] ??= now;
        const age = Math.round(now - born[i]);
        if (age >= duration || !(block instanceof HTMLElement)) continue;
        block.setAttribute('data-arrive', '');
        block.style.animationDelay = `${-age}ms`;
      }
    };
    const observer = new MutationObserver(mark);
    observer.observe(host, { childList: true });
    return () => observer.disconnect();
  };
}
