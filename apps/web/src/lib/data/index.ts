// The one place screens get data from. Today it is the fake replay; the 4CE API client replaces
// it here, behind the same DataSource contract (docs/architecture/web-data-contract.md).
import { createFakeSource } from './fake';
import type { DataSource } from './types';

export const data: DataSource = createFakeSource();

export type * from './types';
