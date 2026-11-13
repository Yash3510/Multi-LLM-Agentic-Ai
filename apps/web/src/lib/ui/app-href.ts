// resolve() for a path held in a variable. Typed as "any in-app path", the argument is a union with
// one member per route, and TypeScript stops checking such a union against resolve()'s per-route
// arguments once it passes 25 members. Every pathname (as opposed to a route id) takes exactly one
// argument, so calling resolve() with the single string is always valid.
import { resolve } from '$app/paths';
import type { PathnameWithSearchOrHash, ResolvedPathname } from '$app/types';

export const appHref = (path: PathnameWithSearchOrHash): ResolvedPathname =>
  (resolve as (path: string) => ResolvedPathname)(path);
