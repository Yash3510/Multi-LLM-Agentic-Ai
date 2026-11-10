// Lets a page open the settings dialog the app shell owns (the admin bar's Settings link).
import { getContext, setContext } from 'svelte';

const KEY = Symbol('open-settings');

export const provideOpenSettings = (open: () => void) => setContext(KEY, open);
export const useOpenSettings = () => getContext<(() => void) | undefined>(KEY);
