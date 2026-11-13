// Whether an address is on this machine or a private network (the owner's rule: model servers
// and other connections stay local or self-hosted). Single-label names such as a container name
// count as local; any dotted public name or public IP does not.

const PRIVATE_V4 = [/^127\./, /^10\./, /^192\.168\./, /^172\.(1[6-9]|2\d|3[01])\./, /^169\.254\./];
const LOCAL_SUFFIXES = ['.local', '.localhost', '.lan', '.internal', '.home.arpa'];

export function isLocalUrl(text: string): boolean {
  let url: URL;
  try {
    url = new URL(text);
  } catch {
    return false;
  }
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return false;
  const host = url.hostname.toLowerCase().replace(/^\[|\]$/g, '');
  if (host === 'localhost' || host === '::1') return true;
  if (/^\d+\.\d+\.\d+\.\d+$/.test(host)) return PRIVATE_V4.some((range) => range.test(host));
  if (host.includes(':')) return /^f[cd]/.test(host);
  if (!host.includes('.')) return true;
  return LOCAL_SUFFIXES.some((suffix) => host.endsWith(suffix));
}
