/* A Svelte action for a container a Word document is drawn into: once the
   first page is there, each of its lines is numbered (--i) and the container
   takes .docx-reveal, which plays the entrance in app.css. Played once. */
export const docxReveal = (node: HTMLElement) => {
	const play = () => {
		if (node.classList.contains('docx-reveal')) return;
		const article = node.querySelector('section.docx > article');
		if (!article) return;
		node.querySelector<HTMLElement>('section.docx > header')?.style.setProperty('--i', '0');
		[...article.children].forEach((line, i) => (line as HTMLElement).style.setProperty('--i', String(i + 1)));
		node.classList.add('docx-reveal');
	};
	const watch = new MutationObserver(play);
	watch.observe(node, { childList: true, subtree: true });
	play();
	return { destroy: () => watch.disconnect() };
};
