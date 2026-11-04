// Third-party notices for the built web app: a Vite plugin that reads which packages actually
// ship in the bundle (its modules and assets) and writes each one's licence text to
// THIRD-PARTY-NOTICES.txt beside the app. MIT, Apache-2.0 and OFL all ask for their notice to
// travel with the copies; a package's own header comment is not always kept by the minifier.
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const MARK = '/node_modules/';

/** The package a module or asset path belongs to, or undefined for the app's own files. */
export function packageOf(id) {
  const path = id.replaceAll('\\', '/');
  const at = path.lastIndexOf(MARK);
  if (path.startsWith('\0') || at < 0) return undefined;
  const parts = path.slice(at + MARK.length).split('/');
  return parts[0].startsWith('@') ? `${parts[0]}/${parts[1]}` : parts[0];
}

function rootOf(id, name) {
  const path = id.replaceAll('\\', '/');
  return path.slice(0, path.lastIndexOf(MARK) + MARK.length) + name;
}

/** A package's name, version, declared licence and the text of its licence file. */
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
 * @param {object} [options]
 * @param {string} [options.root] the app folder, whose package.json lists the runtime dependencies
 *   (fonts and other assets the module list does not show)
 * @param {string[]} [options.include] packages whose content a generator copies into the source
 */
export function thirdPartyNotices({ root = process.cwd(), include = [] } = {}) {
  return {
    name: '4ce-third-party-notices',
    apply: 'build',
    generateBundle(_options, bundle) {
      const roots = new Map();
      for (const item of Object.values(bundle)) {
        const ids = item.type === 'chunk' ? item.moduleIds : (item.originalFileNames ?? []);
        for (const id of ids) {
          const name = packageOf(id);
          if (name && !roots.has(name)) roots.set(name, rootOf(id, name));
        }
      }
      const manifest = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'));
      for (const name of [...Object.keys(manifest.dependencies ?? {}), ...include])
        if (!roots.has(name)) roots.set(name, join(root, 'node_modules', name));
      const packages = [...roots.values()]
        .filter((root) => existsSync(join(root, 'package.json')))
        .map(readPackage);
      this.emitFile({
        type: 'asset',
        fileName: 'THIRD-PARTY-NOTICES.txt',
        source: noticesText(packages),
      });
    },
  };
}
