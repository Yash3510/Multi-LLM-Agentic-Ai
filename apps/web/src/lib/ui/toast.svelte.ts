// Toasts: short confirmations in the top-right corner, as the running app shows them ("Settings
// saved successfully!"). Each closes itself after four seconds or on its close button.
export type ToastKind = 'success' | 'error' | 'info';

interface Toast {
  id: number;
  message: string;
  kind: ToastKind;
}

const SHOW_MS = 4000;
let next = 0;
// Not reactive: only the timers live here.
const timers: Record<number, ReturnType<typeof setTimeout>> = {};

export const toasts = $state<{ list: Toast[] }>({ list: [] });

export function dismiss(id: number) {
  clearTimeout(timers[id]);
  delete timers[id];
  toasts.list = toasts.list.filter((one) => one.id !== id);
}

export function toast(message: string, kind: ToastKind = 'success'): number {
  const id = ++next;
  toasts.list = [...toasts.list, { id, message, kind }];
  timers[id] = setTimeout(() => dismiss(id), SHOW_MS);
  return id;
}
