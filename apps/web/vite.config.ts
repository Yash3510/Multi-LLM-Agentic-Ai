import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { svelteTesting } from '@testing-library/svelte/vite';
import { searchForWorkspaceRoot } from 'vite';
import { defineConfig } from 'vitest/config';

const testing = !!process.env.VITEST;

export default defineConfig({
  plugins: [tailwindcss(), sveltekit(), svelteTesting()],
  // Component tests mount real Svelte components, so they need Svelte's browser build.
  resolve: testing ? { conditions: ['browser'] } : undefined,
  // The repo tools' own tests (tools/*) sit outside this app; only the test run may read them.
  server: testing
    ? { fs: { allow: [searchForWorkspaceRoot(process.cwd()), '../../tools'] } }
    : undefined,
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.ts', '../../tools/**/*.test.mjs'],
  },
});
