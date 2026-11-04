// Hover timing for tooltips and popovers. A pointer has to rest on a trigger for INTENT_MS before
// anything opens, so passing over a toolbar opens nothing; leaving waits GRACE_MS before closing,
// so a pointer that slips off for a moment, or crosses to the popover, does not make it flicker.
// Keyboard focus opens at once, and a key, a blur or a press closes at once.

export const INTENT_MS = 280;
export const GRACE_MS = 160;

export interface GraceClose {
  /** Ask to open or close. Opening is immediate; closing waits out the grace unless `immediate`. */
  request(open: boolean): void;
  /** The next close skips the grace: it was asked for by a key, a blur or a press. */
  immediate(): void;
  /** Drop a pending close, e.g. when the component unmounts. */
  cancel(): void;
}

export function graceClose(setOpen: (open: boolean) => void, grace = GRACE_MS): GraceClose {
  let timer: ReturnType<typeof setTimeout> | undefined;
  let now = false;

  const cancel = () => {
    clearTimeout(timer);
    timer = undefined;
  };

  return {
    request(open) {
      cancel();
      if (open || now) {
        now = false;
        setOpen(open);
        return;
      }
      timer = setTimeout(() => {
        timer = undefined;
        setOpen(false);
      }, grace);
    },
    immediate() {
      now = true;
    },
    cancel,
  };
}
