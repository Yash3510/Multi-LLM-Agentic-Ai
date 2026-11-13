// The words the field components say themselves. Functions, like Paraglide messages, so they can
// move into the message catalogue (en.json, hi.json) without touching the components.
export const fieldText = {
  required: () => 'Required',
  clear: () => 'Clear',
  copy: () => 'Copy',
  copied: () => 'Copied',
  sealed: () => 'Sealed',
  showOptions: () => 'Show options',
  noMatches: () => 'No matches',
  loading: () => 'Loading options',
  matches: (count: number) => (count === 1 ? '1 option' : `${count} options`),
  off: () => 'Off',
  on: () => 'On',
};
