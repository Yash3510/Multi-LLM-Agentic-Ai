// App-wide types for SvelteKit: https://svelte.dev/docs/kit/types#app.d.ts
import type { SkillDraft } from '$lib/ui/skills';

declare global {
  namespace App {
    interface PageState {
      /** A cloned or imported skill the create page starts from (workspace F103, F104). */
      skillDraft?: SkillDraft;
    }
  }
}

export {};
