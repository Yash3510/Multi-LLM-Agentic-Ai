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

describe('fake workspace', () => {
  it('counts each workspace tab and lists models', async () => {
    const source = createFakeSource({ pace: 0 });
    expect(await source.workspaceCounts()).toEqual({
      models: 0,
      knowledge: 3,
      prompts: 0,
      skills: 0,
      tools: 7,
    });
    expect(await source.listModels()).toEqual([]);
  });
});

describe('fake model editor data', () => {
  it('offers the base models, knowledge, tools and skills the capture account has', async () => {
    const source = createFakeSource({ pace: 0 });
    expect((await source.listBaseModels()).map((model) => model.name)).toEqual([
      '4CE / TONY (Orchestrator)',
      'qwen/qwen3-vl-4b',
      'qwen/qwen3-1.7b',
    ]);
    expect(await source.listKnowledge()).toHaveLength(3);
    expect(await source.listTools()).toHaveLength(7);
    expect(await source.listSkills()).toEqual([]);
  });

  it('saves a model into the list and its count', async () => {
    const source = createFakeSource({ pace: 0 });
    await source.saveModel({ id: 'ratio-helper', name: 'Ratio Helper', base: 'qwen/qwen3-1.7b' });
    expect((await source.listModels()).map((model) => model.id)).toEqual(['ratio-helper']);
    expect((await source.workspaceCounts()).models).toBe(1);
    await expect(
      source.saveModel({ id: 'ratio-helper', name: 'Again', base: 'qwen/qwen3-1.7b' }),
    ).rejects.toThrow('ratio-helper');
  });
});

describe('fake knowledge', () => {
  it('lists the stand-in bases with their owner, files and description', async () => {
    const [first] = await createFakeSource({ pace: 0 }).listKnowledge();
    expect(first).toMatchObject({
      name: 'Plant Notes',
      files: 2,
      owner: { name: '4CE Administrator' },
      source: 'local',
      writable: true,
    });
  });

  it('creates a private base at the top and deletes it', async () => {
    const source = createFakeSource({ pace: 0 });
    const made = await source.createKnowledge('Ratio notes', 'Ratios to check.');
    expect((await source.listKnowledge())[0]).toMatchObject({ id: made.id, files: 0 });
    expect((await source.workspaceCounts()).knowledge).toBe(4);
    await source.deleteKnowledge(made.id);
    expect((await source.workspaceCounts()).knowledge).toBe(3);
  });
});

describe('fake knowledge contents', () => {
  const base = 'plant-notes-1';

  it('lists folders first, then documents, with the total', async () => {
    const source = createFakeSource({ pace: 0 });
    const folder = await source.createFolder(base, 'Readings');
    const contents = await source.listContents(base, {});
    expect(contents.folders.map((one) => one.id)).toEqual([folder.id]);
    expect(contents.documents.map((one) => one.name)).toEqual([
      'MEC-014_readings_unit-101B.txt',
      'MEC-014_notes.txt',
    ]);
    expect(contents.total).toBe(3);
  });

  it('searches names, and the text too when asked', async () => {
    const source = createFakeSource({ pace: 0 });
    expect((await source.listContents(base, { query: 'notes' })).documents).toHaveLength(1);
    expect((await source.listContents(base, { query: 'bearing' })).documents).toHaveLength(0);
    expect(
      (await source.listContents(base, { query: 'bearing', content: true })).documents,
    ).toHaveLength(1);
  });

  it('keeps documents inside the folder they were added to', async () => {
    const source = createFakeSource({ pace: 0 });
    const folder = await source.createFolder(base, 'Readings');
    await source.addDocument(base, { name: 'week-1.txt', text: 'Week one.', folder: folder.id });
    expect((await source.listContents(base, { folder: folder.id })).documents).toHaveLength(1);
    expect((await source.listContents(base, {})).documents).toHaveLength(2);
  });

  it('edits, renames and removes documents, and resets the base', async () => {
    const source = createFakeSource({ pace: 0 });
    const [doc] = (await source.listContents(base, {})).documents;
    await source.saveDocumentText(doc.id, 'New text.');
    expect(await source.getDocumentText(doc.id)).toBe('New text.');
    await source.renameItem(base, doc.id, 'renamed.txt');
    expect((await source.listContents(base, {})).documents[0].name).toBe('renamed.txt');
    await source.removeDocument(base, doc.id);
    expect((await source.listContents(base, {})).total).toBe(1);
    await source.resetKnowledge(base);
    expect((await source.listContents(base, {})).total).toBe(0);
  });

  it('deletes a folder with its contents, or moves them up', async () => {
    const source = createFakeSource({ pace: 0 });
    const folder = await source.createFolder(base, 'Old');
    await source.addDocument(base, { name: 'a.txt', text: 'A', folder: folder.id });
    await source.deleteFolder(base, folder.id, { contents: false });
    expect((await source.listContents(base, {})).documents.map((one) => one.name)).toContain(
      'a.txt',
    );
  });
});

describe('fake knowledge record', () => {
  it('opens one base and saves its name and description', async () => {
    const source = createFakeSource({ pace: 0 });
    expect(await source.getKnowledge('missing')).toBeUndefined();
    await source.updateKnowledge('plant-notes-1', { name: 'Unit notes', description: 'Notes.' });
    expect(await source.getKnowledge('plant-notes-1')).toMatchObject({ name: 'Unit notes' });
  });
});

describe('fake prompts', () => {
  const draft = {
    name: 'Summarise',
    command: 'summarise',
    content: 'Summarise {{topic}}.',
    tags: [],
  };

  it('creates a prompt with a live first version, and counts it', async () => {
    const source = createFakeSource({ pace: 0 });
    expect(await source.listPrompts()).toEqual([]);
    const made = await source.createPrompt(draft);
    expect(made).toMatchObject({ command: 'summarise', active: true, writable: true });
    expect((await source.workspaceCounts()).prompts).toBe(1);
    const [first] = await source.listVersions(made.id);
    expect(first).toMatchObject({
      content: 'Summarise {{topic}}.',
      id: made.liveVersion,
      message: 'Initial version',
    });
  });

  it('adds versions, moves the live one, and keeps the live one from deletion', async () => {
    const source = createFakeSource({ pace: 0 });
    const made = await source.createPrompt(draft);
    await source.addVersion(made.id, { content: 'Shorter.', message: 'Trim', live: false });
    const [newest, oldest] = await source.listVersions(made.id);
    expect(newest.message).toBe('Trim');
    expect((await source.getPrompt(made.id))?.content).toBe('Summarise {{topic}}.');
    await source.setLiveVersion(made.id, newest.id);
    expect((await source.getPrompt(made.id))?.content).toBe('Shorter.');
    await expect(source.deleteVersion(made.id, newest.id)).rejects.toThrow();
    await source.deleteVersion(made.id, oldest.id);
    expect(await source.listVersions(made.id)).toHaveLength(1);
  });

  it('switches a prompt off, renames it and deletes it', async () => {
    const source = createFakeSource({ pace: 0 });
    const made = await source.createPrompt(draft);
    await source.setPromptActive(made.id, false);
    await source.updatePrompt(made.id, { name: 'Brief', command: 'brief', tags: ['ops'] });
    expect(await source.getPrompt(made.id)).toMatchObject({ active: false, command: 'brief' });
    await source.deletePrompt(made.id);
    expect(await source.listPrompts()).toEqual([]);
  });
});

describe('fake skills', () => {
  const draft = {
    id: 'ratio-check',
    name: 'Ratio Check',
    description: 'Checks ratios.',
    instructions: '# Ratio check',
  };

  it('creates, lists and counts skills, and refuses a taken id', async () => {
    const source = createFakeSource({ pace: 0 });
    const made = await source.createSkill(draft);
    expect(made).toMatchObject({ id: 'ratio-check', active: true, writable: true });
    expect((await source.workspaceCounts()).skills).toBe(1);
    await expect(source.createSkill(draft)).rejects.toThrow('ratio-check');
  });

  it('edits, switches off and deletes a skill', async () => {
    const source = createFakeSource({ pace: 0 });
    await source.createSkill(draft);
    await source.setSkillActive('ratio-check', false);
    await source.updateSkill('ratio-check', {
      name: 'Ratios',
      description: 'D',
      instructions: 'I',
    });
    expect(await source.getSkill('ratio-check')).toMatchObject({ name: 'Ratios', active: false });
    await source.deleteSkill('ratio-check');
    expect(await source.listSkills()).toEqual([]);
  });
});

describe('fake tools', () => {
  it('lists the stand-in tools with version, description and owner', async () => {
    const [first] = await createFakeSource({ pace: 0 }).listTools();
    expect(first).toMatchObject({
      name: '4CE Sovereignty Check',
      version: '0.1.0',
      owner: { name: '4CE Administrator' },
      writable: true,
    });
  });

  it('creates, edits and deletes a tool, and refuses a taken id', async () => {
    const source = createFakeSource({ pace: 0 });
    const draft = {
      id: 'unit_convert',
      name: 'Unit Convert',
      description: 'Converts',
      content: 'class Tools: pass',
    };
    await source.createTool(draft);
    expect((await source.workspaceCounts()).tools).toBe(8);
    await expect(source.createTool(draft)).rejects.toThrow('unit_convert');
    await source.updateTool('unit_convert', { name: 'Units', description: 'D', content: 'x' });
    expect(await source.getTool('unit_convert')).toMatchObject({ name: 'Units', content: 'x' });
    await source.deleteTool('unit_convert');
    expect(await source.getTool('unit_convert')).toBeUndefined();
  });
});

describe('fake user settings', () => {
  it('starts empty and keeps what is saved, merged', async () => {
    const source = createFakeSource({ pace: 0 });
    expect(await source.getUserSettings()).toEqual({});
    await source.saveUserSettings({ system: 'Be brief.' });
    await source.saveUserSettings({ params: { temperature: 0.5 } });
    expect(await source.getUserSettings()).toEqual({
      system: 'Be brief.',
      params: { temperature: 0.5 },
    });
  });

  it('merges interface choices by key', async () => {
    const source = createFakeSource({ pace: 0 });
    await source.saveUserSettings({ ui: { a: 1 } });
    await source.saveUserSettings({ ui: { b: 2 } });
    expect((await source.getUserSettings()).ui).toEqual({ a: 1, b: 2 });
  });

  it('sets and clears the status, and counts active people', async () => {
    const source = createFakeSource({ pace: 0 });
    await source.setStatus({ emoji: '🛠️', message: 'On site' });
    expect((await source.currentUser())?.status).toEqual({ emoji: '🛠️', message: 'On site' });
    await source.setStatus(undefined);
    expect((await source.currentUser())?.status).toBeUndefined();
    expect(await source.activeUsers()).toBe(1);
  });
});

describe('fake memories', () => {
  it('adds, updates, lists newest first, deletes and clears', async () => {
    const source = createFakeSource({ pace: 0 });
    expect(await source.listMemories()).toEqual([]);
    const first = await source.addMemory({ content: 'Prefers metric units', type: 'user' });
    const second = await source.addMemory({
      content: 'Works on line 3',
      type: 'context',
      path: 'plant/line-3',
    });
    expect((await source.listMemories()).map((one) => one.id)).toEqual([second.id, first.id]);
    await source.updateMemory(first.id, { content: 'Prefers SI units', type: 'user' });
    const listed = await source.listMemories();
    expect(listed[0]).toMatchObject({ id: first.id, content: 'Prefers SI units' });
    await source.deleteMemory(second.id);
    expect(await source.listMemories()).toHaveLength(1);
    await source.clearMemories();
    expect(await source.listMemories()).toEqual([]);
  });
});

describe('fake chat data controls', () => {
  it('exports, imports, archives all and deletes all chats', async () => {
    const source = createFakeSource({ pace: 0 });
    const before = (await source.listChats()).length;
    const exported = await source.exportChats();
    expect(exported).toHaveLength(before);
    expect(exported[0].messages).toBeDefined();
    expect(await source.importChats([{ title: 'Imported run', messages: [] }])).toBe(1);
    expect((await source.listChats()).map((one) => one.title)).toContain('Imported run');
    await source.archiveAllChats();
    expect(await source.listChats()).toEqual([]);
    expect(await source.exportChats()).toHaveLength(before + 1);
    await source.deleteAllChats();
    expect(await source.exportChats()).toEqual([]);
  });
});
