import { describe, expect, it } from 'vitest';
import { createFakeSource } from './fake';
import type { StreamEvent } from './types';

const collect = async (events: AsyncIterable<StreamEvent>) => {
  const seen: StreamEvent[] = [];
  for await (const event of events) seen.push(event);
  return seen;
};

describe('fake source', () => {
  it('lists chats newest first and finds one by id', async () => {
    const source = createFakeSource({ pace: 0 });
    const chats = await source.listChats();
    expect(chats.map((chat) => chat.updated.getTime())).toEqual(
      [...chats].map((chat) => chat.updated.getTime()).sort((a, b) => b - a),
    );
    expect((await source.getChat(chats[0].id))?.messages.length).toBeGreaterThan(0);
    expect(await source.getChat('nope')).toBeUndefined();
  });

  it('streams a run through the chain in time order and stops at the sign-off', async () => {
    const source = createFakeSource({ pace: 0 });
    const events = await collect(source.ask('c-0142', 'Is R2 within the limit?'));
    const times = events.map((event) => event.at);
    expect(times).toEqual([...times].sort((a, b) => a - b));
    const stages = events.flatMap((event) => (event.type === 'status' ? [event.stage] : []));
    for (const role of ['planner', 'reader', 'analyst', 'author', 'challenger', 'sign-off'])
      expect(stages).toContain(role);
    expect(events.some((event) => event.type === 'delta')).toBe(true);
    expect(events.some((event) => event.type === 'tool')).toBe(true);
    expect(events.some((event) => event.type === 'source')).toBe(true);
    expect(events.at(-1)?.type).toBe('sign-off');
  });

  it('finishes with the decision, the receipt and done once the person decides', async () => {
    const source = createFakeSource({ pace: 0 });
    await collect(source.ask('c-0142', 'Is R2 within the limit?'));
    const rest = await collect(source.decide('c-0142', 'released', 'Asha Rao'));
    expect(rest.map((event) => event.type)).toEqual(['decision', 'receipt', 'done']);
  });

  it('stops when the reader aborts', async () => {
    const source = createFakeSource({ pace: 1 });
    const controller = new AbortController();
    const seen: StreamEvent[] = [];
    for await (const event of source.ask('c-0142', 'Is R2 within the limit?', controller.signal)) {
      seen.push(event);
      if (seen.length === 3) controller.abort();
    }
    expect(seen).toHaveLength(3);
  });
});
