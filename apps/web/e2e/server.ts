// A throwaway 4CE server for the sign-in tests, started the repo's own way: `uv run fource-server
// migrate`, then `serve`, as `just dev` does. Usage: node e2e/server.ts PORT, with the accounts as
// JSON in E2E_ACCOUNTS. It runs in a new temporary folder on a fresh SQLite database with a random
// secret, and drops the caller's FOURCE_* variables, so no developer .env or database is touched.
import { spawn, spawnSync } from 'node:child_process';
import { randomBytes } from 'node:crypto';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

// The accounts are added in Python, as apps/server/tests/test_smoke.py does, because
// `fource-server create-user` reads its password from the console, which a test can't type into.
const ADD_ACCOUNTS = `
import asyncio, json, os
from fource.db import Database
from fource.identity import Role, create_user

async def add():
    database = Database(os.environ['FOURCE_DATABASE_URL'])
    try:
        org_id = await database.org_id('default')
        async with database.org_session(org_id) as session:
            for one in json.loads(os.environ['E2E_ACCOUNTS']):
                await create_user(session, email=one['email'], password=one['password'],
                                  roles=[Role.ADMIN], display_name=one['name'])
    finally:
        await database.dispose()

asyncio.run(add())
`;

const port = process.argv[2] ?? '4312';
const folder = mkdtempSync(join(tmpdir(), '4ce-e2e-'));
const env = {
  ...Object.fromEntries(
    Object.entries(process.env).filter(([name]) => !name.startsWith('FOURCE_')),
  ),
  FOURCE_SECRET_KEY: randomBytes(32).toString('hex'),
  FOURCE_DATABASE_URL: `sqlite+aiosqlite:///${join(folder, 'e2e.db').replaceAll('\\', '/')}`,
};
const uv = ['run', '--project', resolve(import.meta.dirname, '../../..')];

for (const step of [
  ['fource-server', 'migrate'],
  ['python', '-c', ADD_ACCOUNTS],
]) {
  const { status } = spawnSync('uv', [...uv, ...step], { cwd: folder, env, stdio: 'inherit' });
  if (status !== 0) process.exit(status ?? 1);
}

const server = spawn('uv', [...uv, 'fource-server', 'serve', '--port', port], {
  cwd: folder,
  env,
  stdio: 'inherit',
});
for (const signal of ['SIGINT', 'SIGTERM'] as const) process.on(signal, () => server.kill(signal));
server.on('exit', (code) => process.exit(code ?? 1));
