import { describe, expect, it } from 'vitest';
import { isLocalUrl } from './local-url';

describe('local or self-hosted addresses (owner rule for connections)', () => {
  it('accepts this machine and private networks', () => {
    for (const url of [
      'http://localhost:1234/v1',
      'http://127.0.0.1:11434',
      'http://[::1]:8080',
      'http://10.0.0.5:8000/v1',
      'http://192.168.1.20:11434',
      'http://172.20.0.3:8080',
      'http://gpu-box.local:8000',
      'http://models.lan/v1',
      'http://host.docker.internal:11434',
      'http://ollama:11434',
    ]) {
      expect(isLocalUrl(url), url).toBe(true);
    }
  });

  it('refuses public hosts and bad input', () => {
    for (const url of [
      'https://api.openai.com/v1',
      'https://example.com',
      'http://8.8.8.8',
      'http://172.32.0.1',
      'ftp://localhost',
      'not a url',
    ]) {
      expect(isLocalUrl(url), url).toBe(false);
    }
  });
});
