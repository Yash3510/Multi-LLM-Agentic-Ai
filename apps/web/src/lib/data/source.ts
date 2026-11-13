// Which data source the app runs on. Until the 4CE API client exists only the fake replay is
// available, and it must never back a production build: such a build refuses to start unless it
// was built as a demo (VITE_4CE_DEMO=1).
import { createFakeSource } from './fake';
import type { DataSource } from './types';

export function chooseSource({
  production,
  demo,
}: {
  production: boolean;
  demo: boolean;
}): DataSource {
  if (production && !demo)
    throw new Error(
      'The fake data source is for dev and demo builds only; build with VITE_4CE_DEMO=1 for a demo, or connect the 4CE API.',
    );
  return createFakeSource();
}
