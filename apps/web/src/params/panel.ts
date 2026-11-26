// The run view's one optional panel (web-screens.md): /runs/[runId]/sign-off is the run view
// with the sign-off panel docked. Any other segment is not this route.
import type { ParamMatcher } from '@sveltejs/kit';

export const match = ((param: string): param is 'sign-off' =>
  param === 'sign-off') satisfies ParamMatcher;
