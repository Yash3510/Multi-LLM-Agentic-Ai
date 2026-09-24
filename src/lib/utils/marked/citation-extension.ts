// 4CE: a citation is one to four source numbers in ascending order - [1],
// [1, 2]. Anything else in square brackets is data the answer is about: read
// as citations, "the median of [5, 3, 9, 1, 7]" became five chips pointing at
// sources that do not exist. The orchestrator applies the same rule
// (_citation in 4ce/functions/orchestrator.py), so the two never disagree
// about what an answer cites.
export const isCitationGroup = (numbers: number[]) =>
	numbers.length > 0 &&
	numbers.length <= 4 &&
	numbers.every((n, i) => Number.isInteger(n) && (i === 0 || n > numbers[i - 1]));

export function citationExtension() {
	return {
		name: 'citation',
		level: 'inline' as const,

		start(src: string) {
			// Trigger on any [number] or [number#suffix]
			// We check for a digit immediately after [ to avoid matching arbitrary links
			return src.search(/\[\d/);
		},

		tokenizer(src: string) {
			// Avoid matching footnotes
			if (/^\[\^/.test(src)) return;

			// Match ONE OR MORE adjacent [1], [1,2], or [1#foo] blocks
			// Example matched: "[1][2,3][4#bar]"
			// We allow: digits, commas, spaces, and # followed by non-control chars (excluding ] and ,)
			const rule = /^(\[(?:\d+(?:#[^,\]\s]+)?(?:,\s*\d+(?:#[^,\]\s]+)?)*)\])+/;
			const match = rule.exec(src);
			if (!match) return;

			const raw = match[0];

			// Extract ALL bracket groups inside the big match
			const groupRegex = /\[([^\]]+)\]/g;
			const ids: number[] = [];
			const citationIdentifiers: string[] = [];
			let m: RegExpExecArray | null;

			while ((m = groupRegex.exec(raw))) {
				// m[1] is the content inside brackets, e.g. "1, 2#foo"
				const parts = m[1].split(',').map((p) => p.trim());
				if (!isCitationGroup(parts.map((p) => parseInt(p, 10)))) return;

				parts.forEach((part) => {
					// Check if it starts with digit
					const match = /^(\d+)(?:#(.+))?$/.exec(part);
					if (match) {
						const index = parseInt(match[1], 10);
						if (!isNaN(index)) {
							ids.push(index);
							// Store the full identifier ("1#foo" or "1")
							citationIdentifiers.push(part);
						}
					}
				});
			}

			if (ids.length === 0) return;

			return {
				type: 'citation',
				raw,
				ids, // merged list of integers for legacy title lookup
				citationIdentifiers // merged list of full identifiers for granular targeting
			};
		},

		renderer(token: any) {
			// fallback text
			return token.raw;
		}
	};
}

export default function () {
	return {
		extensions: [citationExtension()]
	};
}
