// The one place screens get data from. Today it is the fake replay, with sign-in, the session and
// sign-out from the 4CE server in a dev build (source.ts); the server takes over the rest here,
// screen by screen, behind the same DataSource contract (docs/architecture/web-data-contract.md).
import { chooseSource } from './source';
import type { DataSource } from './types';

export const data: DataSource = chooseSource({
  production: import.meta.env.PROD,
  demo: import.meta.env.VITE_4CE_DEMO === '1',
});

export type * from './types';
