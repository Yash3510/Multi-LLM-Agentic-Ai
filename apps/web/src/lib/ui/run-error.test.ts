import { describe, expect, it } from 'vitest';
import { explainRunError } from './run-error';

describe('explainRunError', () => {
  it('reads a server that is not running', () => {
    const e = explainRunError({ detail: 'All connection attempts failed', role: 'Analyst' });
    expect(e).toMatchObject({
      cause: 'server',
      icon: 'plugs',
      title: "The model server isn't running",
    });
    expect(e.subline).toBe('Analyst could not reach the local models.');
    expect(e.steps).toHaveLength(3);
  });

  it('names the model that is not loaded and offers the fix command', () => {
    const e = explainRunError({ detail: 'model "qwen3-8b" not found', role: 'Author' });
    expect(e).toMatchObject({ cause: 'model', command: 'python 4ce/preflight.py --fix' });
    expect(e.subline).toBe('Author was routed to qwen3-8b, which Bionic has not loaded.');
  });

  it('reads too-long and too-slow runs', () => {
    expect(explainRunError({ detail: 'exceeds the available context size' }).cause).toBe('long');
    expect(explainRunError({ detail: 'Request timed out' }).cause).toBe('slow');
  });

  it('falls back to the advice, and to 4CE when no role is known', () => {
    const e = explainRunError({ detail: 'boom', advice: 'Check the logs.' });
    expect(e).toMatchObject({
      cause: 'unknown',
      title: 'The run stopped',
      steps: ['Check the logs.'],
    });
    expect(e.subline).toBe('Something went wrong while 4CE was working.');
  });
});
