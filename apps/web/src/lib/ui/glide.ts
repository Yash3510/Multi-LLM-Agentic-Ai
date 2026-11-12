/**
 * A highlight that slides between resting places instead of jumping (ADR-0042). The attachment
 * adds one marker per kind to the host and lays it over the matching row; glide.css moves it.
 */
export interface GlideOptions {
  /** The row at rest under the active marker, such as `.tab[aria-current]`. */
  active?: string;
  /** Rows the hover marker follows under the pointer. */
  hover?: string;
}

function place(marker: HTMLElement, target: HTMLElement | null) {
  if (!target) {
    delete marker.dataset.on;
    return;
  }
  // A marker that was hidden appears in place: it only slides between two rows.
  const appearing = marker.dataset.on === undefined;
  if (appearing) marker.style.transition = 'none';
  marker.style.setProperty('--glide-x', `${target.offsetLeft}px`);
  marker.style.setProperty('--glide-y', `${target.offsetTop}px`);
  marker.style.setProperty('--glide-w', `${target.offsetWidth}px`);
  marker.style.setProperty('--glide-h', `${target.offsetHeight}px`);
  marker.style.borderRadius = getComputedStyle(target).borderRadius;
  if (appearing) {
    // Reading the box applies the position before the transition comes back.
    void marker.offsetWidth;
    marker.style.transition = '';
  }
  marker.dataset.on = '';
}

export function glide({ active, hover }: GlideOptions) {
  return (host: HTMLElement) => {
    const markers: HTMLElement[] = [];
    const undo: (() => void)[] = [];
    const add = (kind: 'active' | 'hover') => {
      const marker = document.createElement('span');
      marker.dataset.glide = kind;
      marker.setAttribute('aria-hidden', 'true');
      host.prepend(marker);
      markers.push(marker);
      return marker;
    };
    host.dataset.glideHost = '';

    if (active) {
      const marker = add('active');
      const sync = () => place(marker, host.querySelector<HTMLElement>(active));
      const observer = new MutationObserver((records) => {
        // The markers' own style changes are not news.
        if (records.some((record) => !markers.includes(record.target as HTMLElement))) sync();
      });
      observer.observe(host, { subtree: true, childList: true, attributes: true });
      undo.push(() => observer.disconnect());
      if (typeof ResizeObserver !== 'undefined') {
        const resize = new ResizeObserver(sync);
        resize.observe(host);
        undo.push(() => resize.disconnect());
      }
      sync();
    }

    if (hover) {
      const marker = add('hover');
      const over = (event: Event) => {
        const row =
          event.target instanceof Element ? event.target.closest<HTMLElement>(hover) : null;
        place(marker, row && host.contains(row) ? row : null);
      };
      const leave = () => place(marker, null);
      host.addEventListener('pointerover', over);
      host.addEventListener('pointerleave', leave);
      undo.push(() => {
        host.removeEventListener('pointerover', over);
        host.removeEventListener('pointerleave', leave);
      });
    }

    return () => {
      for (const step of undo) step();
      for (const marker of markers) marker.remove();
      delete host.dataset.glideHost;
    };
  };
}
