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

describe('fake usage', () => {
  it('reports totals, a year and a half of days, weekly and running totals', async () => {
    const usage = await createFakeSource({ pace: 0 }).getUsage();
    expect(usage.totals).toMatchObject({ lifetimeTokens: 50_200, userMessages: 6, totalChats: 6 });
    expect(usage.daily.length).toBeGreaterThanOrEqual(540);
    const messages = usage.daily.reduce((sum, day) => sum + day.messages, 0);
    expect(messages).toBe(usage.totals.messages);
    expect(new Date(`${usage.weekly[0].date}T00:00:00Z`).getUTCDay()).toBe(1);
    expect(usage.cumulative.at(-1)?.messages).toBe(messages);
    expect(usage.topModels[0]).toMatchObject({ id: '4ce-tony', messages: 6 });
  });
});

describe('fake archived chats', () => {
  it('lists, unarchives one or all, and deletes one', async () => {
    const source = createFakeSource({ pace: 0 });
    const before = await source.listChats();
    await source.archiveAllChats();
    expect((await source.listArchivedChats()).map((one) => one.id).sort()).toEqual(
      before.map((one) => one.id).sort(),
    );
    await source.unarchiveChat(before[0].id);
    expect((await source.listChats()).map((one) => one.id)).toEqual([before[0].id]);
    await source.deleteChat(before[1].id);
    expect(await source.getChat(before[1].id)).toBeUndefined();
    await source.unarchiveAllChats();
    expect(await source.listArchivedChats()).toEqual([]);
    expect(await source.listChats()).toHaveLength(before.length - 1);
  });
});

describe('fake profile and password', () => {
  it("starts from the person's name, saves the profile and renames them", async () => {
    const source = createFakeSource({ pace: 0 });
    const user = await source.currentUser();
    const profile = await source.getProfile();
    expect(profile).toMatchObject({ name: user?.name, avatar: { kind: 'default' }, variables: {} });
    await source.saveProfile({
      ...profile,
      name: 'Asha Rao',
      gender: 'custom:non-binary',
      variables: { plant_code: 'P3' },
    });
    expect(await source.getProfile()).toMatchObject({
      name: 'Asha Rao',
      gender: 'custom:non-binary',
      variables: { plant_code: 'P3' },
    });
    expect((await source.currentUser())?.name).toBe('Asha Rao');
  });

  it('changes the password only with the current one given', async () => {
    const source = createFakeSource({ pace: 0 });
    await expect(source.changePassword('', 'new-secret')).rejects.toThrow();
    await expect(source.changePassword('old-secret', 'new-secret')).resolves.toBeUndefined();
  });
});

describe('fake admin people', () => {
  it('lists people, adds, edits, deletes and restores, writing a ledger entry each time', async () => {
    const source = createFakeSource({ pace: 0 });
    const people = await source.listUsers();
    expect(people[0]).toMatchObject({ role: 'admin' });
    expect(people[0].created).toBeInstanceOf(Date);

    const added = await source.addUser({
      name: 'Ravi Kumar',
      email: 'ravi@plant.test',
      password: 'demo-only-2',
      role: 'user',
    });
    expect(added).not.toHaveProperty('password');
    await expect(
      source.addUser({ name: 'Again', email: 'RAVI@plant.test', password: 'x', role: 'user' }),
    ).rejects.toThrow(/already/);

    await source.updateUser(added.id, { name: 'Ravi K', email: added.email, role: 'admin' });
    expect((await source.listUsers()).find((one) => one.id === added.id)?.role).toBe('admin');

    await source.deleteUser(added.id);
    expect((await source.listUsers()).some((one) => one.id === added.id)).toBe(false);
    await source.restoreUser(added.id);
    expect((await source.listUsers()).some((one) => one.id === added.id)).toBe(true);

    const ledger = await source.adminLedger();
    expect(ledger.map((entry) => entry.action)).toEqual([
      'user.restore',
      'user.delete',
      'user.update',
      'user.add',
    ]);
    expect(JSON.stringify(ledger)).not.toContain('demo-only-2');
  });
});

describe('fake access preview', () => {
  it('lists the models, knowledge and tools a person can reach', async () => {
    const source = createFakeSource({ pace: 0 });
    const preview = await source.previewAccess('u-admin');
    expect(preview.groups).toEqual([]);
    expect(preview.models.length).toBeGreaterThan(0);
    expect(preview.knowledge.length).toBe((await source.listKnowledge()).length);
    expect(preview.tools.length).toBe((await source.listTools()).length);
  });
});

describe('fake groups', () => {
  it('creates, edits, deletes and restores groups, sets members and default permissions', async () => {
    const source = createFakeSource({ pace: 0 });
    expect(await source.listGroups()).toEqual([]);
    const group = await source.createGroup({
      name: 'Line 3',
      description: 'Night shift',
      share: 'members',
      permissions: {},
    });
    expect(group).toMatchObject({ name: 'Line 3', members: [] });
    await source.setGroupMember(group.id, 'u-admin', true);
    expect((await source.listGroups())[0].members).toEqual(['u-admin']);
    expect((await source.userGroups('u-admin')).map((one) => one.name)).toEqual(['Line 3']);
    await source.updateGroup(group.id, {
      name: 'Line 3A',
      description: '',
      share: 'anyone',
      permissions: { chat: { edit: false } },
    });
    expect((await source.listGroups())[0]).toMatchObject({ name: 'Line 3A', share: 'anyone' });
    await source.deleteGroup(group.id);
    expect(await source.listGroups()).toEqual([]);
    await source.restoreGroup(group.id);
    expect(await source.listGroups()).toHaveLength(1);

    expect(await source.getDefaultPermissions()).toEqual({});
    await source.saveDefaultPermissions({ features: { api_keys: true } });
    expect(await source.getDefaultPermissions()).toEqual({ features: { api_keys: true } });

    expect((await source.adminLedger()).map((entry) => entry.action)).toEqual([
      'permissions.defaults',
      'group.restore',
      'group.delete',
      'group.update',
      'group.member.add',
      'group.add',
    ]);
  });
});

describe('fake evaluations', () => {
  it('starts with no feedback, ranks models from seeded feedback, and deletes and restores', async () => {
    expect(await createFakeSource({ pace: 0 }).listFeedback()).toEqual([]);
    const source = createFakeSource({
      pace: 0,
      feedback: [
        {
          id: 'f1',
          userId: 'u-asha',
          userName: 'Asha Rao',
          modelId: '4ce-tony',
          siblings: ['qwen/qwen3-1.7b'],
          result: 1,
          tags: ['clear'],
          created: new Date(),
          updated: new Date(),
        },
      ],
    });
    const board = await source.leaderboard();
    const winner = board.find((entry) => entry.modelId === '4ce-tony');
    const loser = board.find((entry) => entry.modelId === 'qwen/qwen3-1.7b');
    expect(winner).toMatchObject({ won: 1, lost: 0, tags: [{ tag: 'clear', count: 1 }] });
    expect(loser).toMatchObject({ won: 0, lost: 1 });
    expect((winner?.rating ?? 0) > (loser?.rating ?? 0)).toBe(true);
    expect((await source.modelActivity('4ce-tony', 30)).reduce((n, day) => n + day.won, 0)).toBe(1);
    await source.deleteFeedback('f1');
    expect(await source.listFeedback()).toEqual([]);
    await source.restoreFeedback('f1');
    expect(await source.listFeedback()).toHaveLength(1);
    expect((await source.adminLedger())[0].action).toBe('feedback.restore');
  });
});

describe('fake functions', () => {
  it('lists the stand-in function and reads one by id', async () => {
    const source = createFakeSource({ pace: 0 });
    const [first] = await source.listFunctions();
    expect(first).toMatchObject({
      name: '4CE Orchestrator',
      type: 'pipe',
      version: '0.1.0',
      enabled: true,
    });
    expect((await source.getFunction(first.id))?.content).toContain('class Pipe');
    expect(await source.getFunction('missing')).toBeUndefined();
  });
});

describe('fake admin settings', () => {
  it('keeps each panel apart, merges saves, and logs them', async () => {
    const source = createFakeSource({ pace: 0 });
    expect(await source.getAdminSettings('general')).toEqual({});
    await source.saveAdminSettings('general', { ENABLE_CHANNELS: true });
    await source.saveAdminSettings('general', { ENABLE_NOTES: false });
    expect(await source.getAdminSettings('general')).toEqual({
      ENABLE_CHANNELS: true,
      ENABLE_NOTES: false,
    });
    expect(await source.getAdminSettings('authentication')).toEqual({});
    expect((await source.adminLedger())[0]).toMatchObject({ action: 'settings.general' });
  });
});

describe('fake admin data export and config import', () => {
  it('exports config, chats and users, imports config with the old one kept for undo, and logs each', async () => {
    const source = createFakeSource({ pace: 0 });
    await source.saveAdminSettings('general', { ENABLE_CHANNELS: true });
    expect(JSON.parse((await source.exportAdminData('config')) ?? '')).toEqual({
      general: { ENABLE_CHANNELS: true },
    });
    expect(JSON.parse((await source.exportAdminData('chats')) ?? '[]').length).toBeGreaterThan(0);
    expect((await source.exportAdminData('users'))?.split('\n')[0]).toBe('id,name,email,role');
    expect(await source.exportAdminData('database')).toBeUndefined();
    const previous = await source.importAdminConfig({ general: { ENABLE_NOTES: false } });
    expect(await source.getAdminSettings('general')).toEqual({ ENABLE_NOTES: false });
    await source.importAdminConfig(previous);
    expect(await source.getAdminSettings('general')).toEqual({ ENABLE_CHANNELS: true });
    const actions = (await source.adminLedger()).map((entry) => entry.action);
    expect(actions.slice(0, 5)).toEqual([
      'config.import',
      'config.import',
      'export.users',
      'export.chats',
      'export.config',
    ]);
  });
});

describe('fake admin maintenance', () => {
  it('logs each maintenance task', async () => {
    const source = createFakeSource({ pace: 0 });
    await source.adminMaintenance('reset-vectors');
    expect((await source.adminLedger())[0].action).toBe('maintenance.reset-vectors');
  });
});

describe('fake analytics', () => {
  it('summarises messages, tokens, chats and people per day, by model and by person', async () => {
    const analytics = await createFakeSource({ pace: 0 }).getAnalytics(7);
    expect(analytics.totals).toEqual({ messages: 3, tokens: 4400, chats: 2, users: 1 });
    expect(analytics.daily).toHaveLength(8);
    expect(analytics.daily.reduce((sum, day) => sum + day.messages, 0)).toBe(3);
    expect(analytics.models[0]).toMatchObject({ id: '4ce-tony', messages: 3, users: 1, chats: 2 });
    expect(analytics.users[0]).toMatchObject({
      name: '4CE Administrator',
      messages: 3,
      tokens: 4400,
    });
  });
});

describe('fake notes', () => {
  it('creates, edits, deletes and restores notes, and streams an enhanced version', async () => {
    const source = createFakeSource({ pace: 0 });
    expect(await source.listNotes()).toEqual([]);
    const note = await source.createNote({
      title: 'Weekly review',
      content: 'item 3 needs review',
    });
    await source.updateNote(note.id, {
      title: 'Weekly review',
      content: 'Item 3 needs a second look.',
    });
    expect((await source.getNote(note.id))?.content).toBe('Item 3 needs a second look.');
    let text = '';
    for await (const piece of source.enhanceNote('item 3 needs review')) text += piece;
    expect(text.length).toBeGreaterThan(0);
    await source.deleteNote(note.id);
    expect(await source.listNotes()).toEqual([]);
    await source.restoreNote(note.id);
    expect(await source.listNotes()).toHaveLength(1);
  });
});
