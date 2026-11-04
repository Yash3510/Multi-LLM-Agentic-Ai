<script lang="ts">
  // A link: ink text with an underline, in prose or on its own. It takes the surrounding type step.
  // In-app paths are typed against the routes and get the base path here, so callers never build
  // hrefs by hand. `external` marks a link that leaves the app: rel="external" (no client routing)
  // and an arrow; where it opens is the caller's call. aria-current draws the current state.
  import { resolve } from '$app/paths';
  import type { PathnameWithSearchOrHash } from '$app/types';
  import type { Snippet } from 'svelte';
  import type { HTMLAnchorAttributes } from 'svelte/elements';
  import Icon from '$lib/ui/icons/Icon.svelte';
  import './actions.css';

  type Props = Omit<HTMLAnchorAttributes, 'href'> & { children: Snippet } & (
      | { href: PathnameWithSearchOrHash; external?: false; externalLabel?: never }
      | {
          /** Any URL outside the app. */
          href: string;
          external: true;
          /** Spoken for the arrow, e.g. "leaves 4CE"; without it the arrow is decoration only. */
          externalLabel?: string;
        }
    );

  let { href, external = false, externalLabel, children, ...rest }: Props = $props();
</script>

<!-- A no-break space before the arrow: it never wraps alone, and the spoken note stays a word. -->
{#if external}
  <a {href} rel="external" data-link="" {...rest}
    >{@render children()}&nbsp;<Icon name="arrow-up-right" size={16} />{#if externalLabel}<span
        class="sr-only">{externalLabel}</span
      >{/if}</a
  >
{:else}
  <!-- The union above guarantees an in-app path on this branch. -->
  <a href={resolve(href as PathnameWithSearchOrHash)} data-link="" {...rest}>{@render children()}</a
  >
{/if}
