import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { svelteTesting } from '@testing-library/svelte/vite';
import { searchForWorkspaceRoot, type Plugin } from 'vite';
import { defineConfig } from 'vitest/config';
import { noticesFor } from '../../tools/notices/notices.mjs';

const testing = !!process.env.VITEST;

// Writes the licence text of every package the build ships to THIRD-PARTY-NOTICES.txt.
const thirdPartyNotices = (include: string[]): Plugin => ({
  name: '4ce-third-party-notices',
  apply: 'build',
  generateBundle(_options, bundle) {
    const ids = Object.values(bundle).flatMap((item) =>
      item.type === 'chunk' ? item.moduleIds : item.originalFileNames,
    );
    this.emitFile({
      type: 'asset',
      fileName: 'THIRD-PARTY-NOTICES.txt',
      source: noticesFor(ids, import.meta.dirname, include),
    });
  },
});

export default defineConfig({
  plugins: [
    tailwindcss(),
    sveltekit(),
    svelteTesting(),
    // The icon paths are generated from @phosphor-icons/core into the source, so it is named here.
    thirdPartyNotices(['@phosphor-icons/core']),
  ],
  // Vite 8 drops legal comments when it minifies; keep them so third-party notices (the Phosphor
  // MIT licence on the icon table) ship in the built app.
  build: { rolldownOptions: { output: { comments: { legal: true } } } },
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
