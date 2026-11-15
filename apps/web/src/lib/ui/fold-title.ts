// A provenance fold's title, split so the row can set each part in its own type: the role and its
// step, a verdict (PASS or FAIL) in the verdict colour, and the model in Plex Mono. The receipt
// writes titles as "Role — step — VERDICT · provider/model".
export interface FoldTitle {
  text: string;
  verdict?: 'PASS' | 'FAIL';
  model?: string;
}

export function foldTitle(title: string): FoldTitle {
  const dot = title.lastIndexOf(' · ');
  const tail = dot > 0 ? title.slice(dot + 3) : '';
  const model = tail.includes('/') ? tail : undefined;
  const head = model ? title.slice(0, dot) : title;
  const parts = head.split(' — ');
  const verdict = parts.find((part): part is 'PASS' | 'FAIL' => part === 'PASS' || part === 'FAIL');
  const text = parts.filter((part) => part !== verdict).join(' · ');
  return { text, ...(verdict ? { verdict } : {}), ...(model ? { model } : {}) };
}
