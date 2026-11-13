import js from '@eslint/js';
import { defineConfig, globalIgnores } from 'eslint/config';
import svelte from 'eslint-plugin-svelte';
import globals from 'globals';
import ts from 'typescript-eslint';
import svelteConfig from './svelte.config.js';

export default defineConfig(
  globalIgnores([
    'build/',
    '.svelte-kit/',
    'coverage/',
    'test-results/',
    'playwright-report/',
    'src/lib/ui/icons/generated/',
    'src/lib/i18n/generated/',
  ]),
  js.configs.recommended,
  ts.configs.recommended,
  svelte.configs.recommended,
  {
    languageOptions: {
      globals: { ...globals.browser, ...globals.node },
      // Type information lets rules such as svelte/no-navigation-without-resolve recognise a
      // value typed ResolvedPathname (lib/ui/app-href.ts) as already resolved.
      parserOptions: {
        projectService: { allowDefaultProject: ['eslint.config.js', 'svelte.config.js'] },
        tsconfigRootDir: import.meta.dirname,
      },
    },
    // TypeScript already reports undefined names, with type information ESLint lacks.
    rules: { 'no-undef': 'off' },
  },
  {
    files: ['**/*.svelte', '**/*.svelte.ts', '**/*.svelte.js'],
    languageOptions: {
      parserOptions: {
        parser: ts.parser,
        extraFileExtensions: ['.svelte'],
        svelteConfig,
        projectService: { allowDefaultProject: ['eslint.config.js', 'svelte.config.js'] },
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
);
