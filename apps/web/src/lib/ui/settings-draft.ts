// Whether the General page holds anything unsaved: the save bar shows only then (ADR-0041
// amendment, 2026-11-13). A prompt of spaces alone saves as no prompt, so it counts as none.
import type { ParamValue } from './params';

type Params = Record<string, ParamValue>;

const prompt = (text: string | undefined) => (text?.trim() ? text : '');

export function draftChanged(
  saved: { system?: string; params: Params },
  system: string,
  params: Params,
): boolean {
  if (prompt(saved.system) !== prompt(system)) return true;
  const keys = Object.keys(params);
  return (
    keys.length !== Object.keys(saved.params).length ||
    keys.some((key) => params[key] !== saved.params[key])
  );
}
