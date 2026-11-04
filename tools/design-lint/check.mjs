// Design lint for apps/web (ADR-0041 §3: retuned to the measured look; ADR-0035 §13).
// Usage: node tools/design-lint/check.mjs [dir]   (default: apps/web/src)
// Prints file:line:column for every hit and exits 1 if there is any.
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, extname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const DEFAULT_ROOT = resolve(HERE, '../../apps/web/src');
const EXTENSIONS = new Set(['.svelte', '.ts', '.js', '.mjs', '.css', '.html']);
// Only the token files may hold raw colour values.
const TOKENS_DIR = 'lib/ui/tokens/';
// The html shell paints its splash before any stylesheet loads, so it may name a token's exact
// value (ADR-0041 amendment); any other hex there still fails.
const SHELL = 'app.html';
// Generator output is checked at its source: the generators reject what this lint rejects.
const SKIPPED_DIRS = ['lib/i18n/generated', 'lib/ui/icons/generated'];

// The measured look's largest scale is the loading dot's 1.25 pulse.
const MAX_SCALE = 1.25;

/** Is a CSS scale factor above the cap? Percentages count too (scale: 130%). */
const aboveCap = (raw) => {
  const value = raw.endsWith('%') ? parseFloat(raw) / 100 : parseFloat(raw);
  return Number.isFinite(value) && value > MAX_SCALE;
};

export const RULES = [
  {
    id: 'hex-colour',
    message: 'hex colour outside the token files; use a semantic token',
    pattern: /(?<![\w&#])#(?:[0-9a-f]{8}|[0-9a-f]{6}|[0-9a-f]{3,4})(?![\w-])/gi,
    allowInTokens: true,
  },
  {
    id: 'drop-shadow',
    message: 'drop-shadow filters are banned; depth comes from the elevation tokens',
    pattern: /drop-shadow/g,
  },
  {
    id: 'arbitrary-value',
    message: 'arbitrary value; use a token utility',
    pattern: /(?<![\w$-])(?:[a-z-]+:)*-?[a-z][a-z0-9-]*-(?:\[[^\]\s'"`]+\]|\(--[\w-]+\))/g,
  },
  {
    id: 'scale-above-cap',
    message: 'nothing scales above 1.25',
    // Utility classes (scale-105), CSS functions (scale(1.02)) and the scale property or key.
    pattern:
      /(?<![\w-])(?:[a-z-]+:)*-?scale(?:-[xyz])?-(\d+)(?![\w-])|(?<![\w-])scale(?:3d|X|Y|Z)?\(([^)]*)\)|(?<![\w-])scale:\s*([^;}'"\n,]+)/g,
    accept: (m) =>
      m[1] !== undefined
        ? Number(m[1]) > MAX_SCALE * 100
        : (m[2] ?? m[3]).split(/[\s,]+/).filter(Boolean).some(aboveCap),
  },
];

/** Every rule hit in one file's text. `inTokens` relaxes the colour rules for token files;
 * `tokenHexes` (lower case) are hex values the text may use as they are. */
export function lintText(text, { inTokens = false, tokenHexes = new Set() } = {}) {
  const hits = [];
  text.split('\n').forEach((line, index) => {
    for (const rule of RULES) {
      if (inTokens && rule.allowInTokens) continue;
      for (const match of line.matchAll(rule.pattern)) {
        if (rule.accept && !rule.accept(match)) continue;
        if (rule.allowInTokens && tokenHexes.has(match[0].toLowerCase())) continue;
        hits.push({ line: index + 1, column: match.index + 1, rule: rule.id, text: match[0] });
      }
    }
  });
  return hits;
}

const relativeTo = (root, path) => relative(root, path).split(sep).join('/');

function* walk(root, dir = root) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!SKIPPED_DIRS.includes(relativeTo(root, path))) yield* walk(root, path);
    } else if (EXTENSIONS.has(extname(entry.name))) yield path;
  }
}

/** Every rule hit under `root` (an apps/web/src-shaped tree). */
export function lintDir(root) {
  const hits = [];
  const paths = [...walk(root)];
  const hex = RULES.find((rule) => rule.id === 'hex-colour').pattern;
  const tokenHexes = new Set(
    paths
      .filter((path) => relativeTo(root, path).startsWith(TOKENS_DIR))
      .flatMap((path) => [...readFileSync(path, 'utf8').matchAll(hex)])
      .map((match) => match[0].toLowerCase()),
  );
  for (const path of paths) {
    const where = relativeTo(root, path);
    const inTokens = where.startsWith(TOKENS_DIR);
    const options = { inTokens, tokenHexes: where === SHELL ? tokenHexes : undefined };
    for (const hit of lintText(readFileSync(path, 'utf8'), options)) {
      hits.push({ file: path, ...hit });
    }
  }
  return hits;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const root = resolve(process.argv[2] ?? DEFAULT_ROOT);
  let hits;
  try {
    hits = lintDir(root);
  } catch (error) {
    console.error(`design-lint: cannot read ${root}: ${error.message}`);
    process.exit(2);
  }
  for (const hit of hits) {
    const where = `${relative(process.cwd(), hit.file)}:${hit.line}:${hit.column}`;
    const message = RULES.find((rule) => rule.id === hit.rule).message;
    console.log(`${where}  ${hit.rule}  ${hit.text.trim()}  (${message})`);
  }
  if (hits.length > 0) {
    console.error(`design-lint: ${hits.length} problem${hits.length === 1 ? '' : 's'}`);
    process.exit(1);
  }
  console.log('design-lint: clean');
}
