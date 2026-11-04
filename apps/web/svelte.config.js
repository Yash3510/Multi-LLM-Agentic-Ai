import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    // 4ce-server returns 200.html for every path that is not /api or /ws (ADR-0035 §2),
    // and serves the precompressed files as they are.
    adapter: adapter({ fallback: '200.html', precompress: true }),
    // Browser tests live outside src, so the generated tsconfig has to be told to check them.
    typescript: {
      config: (tsconfig) => {
        tsconfig.include.push('../playwright.config.ts', '../e2e/**/*.ts');
      },
    },
  },
};

export default config;
