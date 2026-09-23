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
