/* How an evidence chip names its document: a document code such as
   "SOP-MEC-014" when the name starts with one, otherwise the name without its
   extension or underscores. When another source shares the code (the SOP
   and a log of readings against it), the rest of the name follows it, so two
   chips never read the same. The full file name is on hover and in the
   passage panel. */
const bare = (title: string) => title.replace(/\.(pdf|docx?|md|txt|csv|xlsx?|pptx?|html?)$/i, '');
const codeOf = (name: string) => name.match(/^[A-Z]{2,}(?:-[A-Z0-9]+)*-\d+/)?.[0] ?? null;

export const chipTitle = (title: string, others: string[] = []) => {
	const name = bare(title);
	const code = codeOf(name);
	if (!code) return name.replace(/_+/g, ' ');
	const shared = others.filter(Boolean).some((other) => other !== title && codeOf(bare(other)) === code);
	const rest = name.slice(code.length).replace(/^[\s_\-–—.]+/, '').replace(/_+/g, ' ').trim();
	return shared && rest ? `${code} · ${rest}` : code;
};

/* One look for every evidence chip: the chat's ink on a quiet fill, a
   document's page for an icon. */
export const CHIP =
	'evidence-chip inline-flex w-fit max-w-[16rem] translate-y-[1px] items-center gap-1 rounded-full border border-gray-200 bg-gray-50 px-1.5 py-px align-baseline text-[0.66rem] font-medium leading-[1.35] text-gray-700 transition hover:border-gray-300 hover:bg-gray-100 hover:text-gray-900 dark:border-gray-700 dark:bg-gray-850 dark:text-gray-200 dark:hover:border-gray-600 dark:hover:bg-gray-800 dark:hover:text-white';

/* A check line a small verifier cut off mid-sentence ("This is a claim that
   is") tells a reviewer nothing, and shown with a cross it reads as a failed
   check. Such a line ends on a word no sentence ends on; it is left out of
   every list of checks. The record itself is unchanged. */
const DANGLING = new Set(
	(
		'a an the is are was were be been being of to in on at by for with from that which who whose ' +
		'and or but if as than so because while when where this these those not very more most their ' +
		'our your his her its'
	).split(' ')
);
export const isFragment = (text: string) => {
	const t = String(text ?? '')
		.trim()
		.replace(/[\s,;:\-–—]+$/, '');
	if (!t) return true;
	if (/[.!?)"”'’\]]$/.test(t)) return false;
	const last = (t.split(/\s+/).pop() ?? '').toLowerCase().replace(/[^a-z']/g, '');
	return DANGLING.has(last);
};
export const usableChecks = <T extends { text?: string }>(checks: T[] | null | undefined): T[] =>
	(checks ?? []).filter((c) => !isFragment(c?.text ?? ''));
