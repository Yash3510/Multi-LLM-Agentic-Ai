/* Word's own bullets are private-use characters in the Symbol and Wingdings
   fonts ("" is the round bullet), which a browser draws as an empty
   box. docx-preview copies them into its generated styles as they are; this
   swaps each for the Unicode character it stands for, after a render. */
const SYMBOL_BULLETS: Record<string, string> = {
	'': '•',
	'': '▪',
	'': '■',
	'': '➢',
	'': '❖',
	'': '✓'
};

export const fixDocxBullets = (root: HTMLElement | null | undefined) => {
	for (const style of root?.querySelectorAll('style') ?? []) {
		const text = style.textContent ?? '';
		const fixed = text
			.replace(/[-]/g, (c) => SYMBOL_BULLETS[c] ?? '•')
			.replace(/font-family:\s*(?:Symbol|Wingdings)\s*;/gi, '');
		if (fixed !== text) style.textContent = fixed;
	}
};
