<script context="module">
	import { marked } from 'marked';

	import markedExtension from '$lib/utils/marked/extension';
	import markedKatexExtension from '$lib/utils/marked/katex-extension';
	import { disableSingleTilde } from '$lib/utils/marked/strikethrough-extension';
	import { mentionExtension } from '$lib/utils/marked/mention-extension';
	import colonFenceExtension from '$lib/utils/marked/colon-fence-extension';
	import footnoteExtension from '$lib/utils/marked/footnote-extension';
	import citationExtension from '$lib/utils/marked/citation-extension';

	const options = {
		throwOnError: false
	};

	marked.use(markedKatexExtension(options));
	marked.use(markedExtension(options));
	marked.use(citationExtension(options));
	marked.use(footnoteExtension(options));
	marked.use(colonFenceExtension(options));
	marked.use(disableSingleTilde);
	marked.use({
		extensions: [
			mentionExtension({ triggerChar: '@' }),
			mentionExtension({ triggerChar: '#' }),
			mentionExtension({ triggerChar: '$' })
		]
	});
</script>

<script>
	import { onDestroy } from 'svelte';
	import { replaceTokens, processResponseContent } from '$lib/utils';
	import { user } from '$lib/stores';

	import MarkdownTokens from './Markdown/MarkdownTokens.svelte';

	export let id = '';
	export let chatId = '';
	export let messageId = '';
	export let content;
	export let done = true;
	export let model = null;
	export let save = false;
	export let preview = false;
	export let compactPreview = false;

	export let paragraphTag = 'p';
	export let editCodeBlock = true;
	export let topPadding = false;
	export let allowEmbeds = true;

	export let sourceIds = [];

	export let onSave = () => {};
	export let onUpdate = () => {};

	export let onPreview = () => {};

	export let onSourceClick = () => {};
	export let onTaskClick = () => {};
	export let onToolCallResolved = () => {};

	let tokens = [];
	let pendingUpdate = null;
	let lastContent = '';
	let lastParsedContent = '';

	/* 4CE answers released before the report became a card end with its
	   download as a line of text, after a rule; drawn as the same card. */
	const REPORT_LINE =
		/(?:\n---\n\n)?\*\*([^*\n]+)\*\* · ([^\n]+?) · (\d+) KB, stored on this machine · \[Download [^\]\n]*\]\((\/api\/v1\/files\/[^)\s]+)\)/g;
	const reportCards = (text) =>
		text.includes('stored on this machine')
			? text.replace(
					REPORT_LINE,
					(_, kind, title, kb, url) =>
						'\n```4ce-file\n' + JSON.stringify({ kind, title, kb: Number(kb), url }) + '\n```'
				)
			: text;

	const parseTokens = () => {
		if (content === lastContent) return;
		lastContent = content;

		const processed = replaceTokens(
			processResponseContent(reportCards(content)),
			model?.name,
			$user?.name
		);
		if (processed === lastParsedContent) return;
		lastParsedContent = processed;

		tokens = marked.lexer(processed);
	};

	const updateHandler = (content) => {
		if (content) {
			if (done) {
				cancelAnimationFrame(pendingUpdate);
				pendingUpdate = null;
				parseTokens();
			} else if (!pendingUpdate) {
				pendingUpdate = requestAnimationFrame(() => {
					pendingUpdate = null;
					parseTokens();
				});
			}
		}
	};

	$: updateHandler(content);

	// Throttle parsing to once per animation frame while streaming
	onDestroy(() => {
		cancelAnimationFrame(pendingUpdate);
	});
</script>

{#key id}
	<MarkdownTokens
		{tokens}
		{id}
		{chatId}
		{messageId}
		{done}
		{save}
		{preview}
		{compactPreview}
		{paragraphTag}
		{editCodeBlock}
		{sourceIds}
		{topPadding}
		{allowEmbeds}
		{onTaskClick}
		{onSourceClick}
		{onToolCallResolved}
		{onSave}
		{onUpdate}
		{onPreview}
	/>
{/key}
