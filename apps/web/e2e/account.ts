// The accounts on the sign-in tests' throwaway server (e2e/server.ts adds them). The second one is
// only for the lockout test, so the first never locks.
export const ACCOUNTS = [
  { email: 'ada@example.com', name: 'Ada Lovelace', password: 'correct horse battery staple' },
  { email: 'grace@example.com', name: 'Grace Hopper', password: 'another horse battery staple' },
];
