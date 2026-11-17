// Which data source the app runs on (ADR-0046). A demo build (VITE_4CE_DEMO=1) is the fake replay
// throughout and needs no server. A dev build takes sign-in, the session and sign-out from the
// 4CE server and everything else from the fake replay, until the server serves each screen. A
// production build must never show stand-in data, so it refuses to start until then.
import { createFakeSource } from './fake';
import { serverSession } from './server';
import type { DataSource } from './types';

export function chooseSource({
  production,
  demo,
}: {
  production: boolean;
  demo: boolean;
}): DataSource {
  if (demo) return createFakeSource();
  if (production)
    throw new Error(
      'The fake data source is for dev and demo builds only; build with VITE_4CE_DEMO=1 for a demo, or connect the 4CE API.',
    );
  return { ...createFakeSource(), ...serverSession() };
}
