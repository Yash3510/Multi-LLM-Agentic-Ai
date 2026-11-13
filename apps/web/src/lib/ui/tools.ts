// Tool rules (workspace F112, F114): the id made from the name, the code's header block, the
// starter code, and JSON import and export.

export interface ToolDraft {
  id: string;
  name: string;
  description: string;
  content: string;
}

/** Accents stripped, runs of anything but letters and digits to one underscore, lowercased. */
export const toolId = (name: string) =>
  name
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');

/** "key: value" lines in a triple-quoted block at the very top of the code. */
export function manifest(code: string): Record<string, string> {
  const block = /^"""\n([\s\S]*?)\n"""/.exec(code);
  if (!block) return {};
  return Object.fromEntries(
    block[1]
      .split('\n')
      .map((line) => /^([\w-]+):\s*(.*)$/.exec(line))
      .filter((match): match is RegExpExecArray => match !== null)
      .map(([, key, value]) => [key, value.trim()]),
  );
}

/** The code a new tool starts from: the class shape the server expects, with two offline
 * examples. Written for 4CE (the owner chose not to carry over the running app's sample). */
export const STARTER = `"""
title: My Tool
version: 0.1.0
"""

from datetime import datetime


class Tools:
    def __init__(self):
        pass

    # Each method is a tool the model can call. Give every argument a type hint and describe
    # the tool in its docstring: the model reads both to decide when and how to use it.

    def current_time(self) -> str:
        """
        Get the current date and time on this server.
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def convert_length(self, value: float, unit_from: str, unit_to: str) -> str:
        """
        Convert a length between millimetres, centimetres, metres and kilometres.
        :param value: The length to convert.
        :param unit_from: One of mm, cm, m, km.
        :param unit_to: One of mm, cm, m, km.
        """
        metres = {"mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0}
        if unit_from not in metres or unit_to not in metres:
            return "Units must be mm, cm, m or km."
        result = value * metres[unit_from] / metres[unit_to]
        return f"{value} {unit_from} = {result:g} {unit_to}"
`;

/** An imported JSON file's tools, sent as they are (F112). */
export function readToolFile(json: string): ToolDraft[] {
  const parsed: unknown = JSON.parse(json);
  if (!Array.isArray(parsed)) throw new Error('The file must hold a list of tools.');
  return parsed as ToolDraft[];
}

/** Saves tools as a JSON file named with the time (F107, F111). */
export function saveToolFile(tools: object[], name = 'tools-export') {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(tools, null, 2)], { type: 'application/json' }),
  );
  Object.assign(document.createElement('a'), {
    href: url,
    download: `${name}-${Date.now()}.json`,
  }).click();
  URL.revokeObjectURL(url);
}
