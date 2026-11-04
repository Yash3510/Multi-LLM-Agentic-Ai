// Third-party notices for the built web app: from the packages that actually ship in the bundle
// (its modules and assets), each one's licence text for THIRD-PARTY-NOTICES.txt beside the app
// (the Vite plugin in apps/web/vite.config.ts calls noticesFor). MIT, Apache-2.0 and OFL all ask for their notice to
// travel with the copies; a package's own header comment is not always kept by the minifier.
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const MARK = '/node_modules/';

/** @typedef {{ name: string, version: string, license: string, text: string }} Notice */

/**
 * The package a module or asset path belongs to, or undefined for the app's own files.
 * @param {string} id
 * @returns {string | undefined}
 */
export function packageOf(id) {
  const path = id.replaceAll('\\', '/');
  const at = path.lastIndexOf(MARK);
  if (path.startsWith('\0') || at < 0) return undefined;
  const parts = path.slice(at + MARK.length).split('/');
  return parts[0].startsWith('@') ? `${parts[0]}/${parts[1]}` : parts[0];
}

/** @param {string} id @param {string} name */
function rootOf(id, name) {
  const path = id.replaceAll('\\', '/');
  return path.slice(0, path.lastIndexOf(MARK) + MARK.length) + name;
}

/**
 * A package's name, version, declared licence and the text of its licence file.
 * @param {string} root
 * @returns {Notice}
 */
export function readPackage(root) {
  const manifest = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'));
  const file = readdirSync(root).find((entry) => /^(licen[cs]e|copying)(\.|$)/i.test(entry));
  return {
    name: manifest.name,
    version: manifest.version,
    license: manifest.license ?? 'unknown',
    text: file ? readFileSync(join(root, file), 'utf8').trim() : '',
  };
}

/** @param {Notice[]} packages */
export function noticesText(packages) {
  const unique = [...new Map(packages.map((entry) => [entry.name, entry])).values()].sort((a, b) =>
    a.name.localeCompare(b.name),
  );
  const sections = unique.map(
    ({ name, version, license, text }) =>
      `${name} ${version}\nLicence: ${license}\n\n${text || 'No licence file in the package.'}`,
  );
  return `Third-party notices for the 4CE web app.\n\n${sections.join(`\n\n${'-'.repeat(72)}\n\n`)}\n`;
}

/**
 * The notices for the files a build ships: `ids` are its module ids and asset source paths,
 * `root` the app folder (its runtime dependencies cover fonts and other assets), and `include`
 * names packages whose content a generator copies into the source.
 * @param {Iterable<string>} ids
 * @param {string} root
 * @param {string[]} [include]
 */
export function noticesFor(ids, root, include = []) {
  /** @type {Map<string, string>} */
  const roots = new Map();
  for (const id of ids) {
    const name = packageOf(id);
    if (name && !roots.has(name)) roots.set(name, rootOf(id, name));
  }
  const manifest = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'));
  for (const name of [...Object.keys(manifest.dependencies ?? {}), ...include])
    if (!roots.has(name)) roots.set(name, join(root, 'node_modules', name));
  return noticesText(
    [...roots.values()].filter((dir) => existsSync(join(dir, 'package.json'))).map(readPackage),
  );
}
