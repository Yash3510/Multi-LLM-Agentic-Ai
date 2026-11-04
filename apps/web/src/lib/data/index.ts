// The one place screens get data from. Today it is the fake replay (dev and demo builds only);
// the 4CE API client replaces it here, behind the same DataSource contract
// (docs/architecture/web-data-contract.md).
import { chooseSource } from './source';
import type { DataSource } from './types';

export const data: DataSource = chooseSource({
  production: import.meta.env.PROD,
  demo: import.meta.env.VITE_4CE_DEMO === '1',
});

export type * from './types';
