<script lang="ts" context="module">
	// When this page was opened, in the seconds messages are stamped with. Only
	// a message newer than this rises in; opening an old chat draws it still.
	const OPENED_AT = Math.floor(Date.now() / 1000);
</script>

<script lang="ts">
	import { toast } from 'svelte-sonner';

	import { tick, getContext, onMount, createEventDispatcher } from 'svelte';
	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	import { settings } from '$lib/stores';
	import { copyToClipboard } from '$lib/utils';

	import MultiResponseMessages from './MultiResponseMessages.svelte';
	import ResponseMessage from './ResponseMessage.svelte';
	import UserMessage from './UserMessage.svelte';

	export let chatId;
	export let selectedModels = [];
	export let idx = 0;

	export let history;
	export let messageId;

	export let user;

	export let setInputText: Function = () => {};
	export let gotoMessage;
	export let showPreviousMessage;
	export let showNextMessage;
	export let updateChat;

	export let editMessage;
	export let saveMessage;
	export let deleteMessage;
	export let rateMessage;
	export let actionMessage;
	export let submitMessage;

	export let regenerateResponse;
	export let continueResponse;
	export let mergeResponses;

	export let addMessages;
	export let onToolCallResolved: Function = () => {};
	export let forkHandler: Function | null = null;
	export let triggerScroll;
	export let readOnly = false;
	export let allowDelete = true;
	export let compactPreview = false;
	export let editCodeBlock = true;
	export let topPadding = false;
	export let onInsertToNote: ((content: string) => void) | null = null;

	// Safari's content-visibility implementation has paint bugs that leave
	// on-screen messages blank (#26712), so skip virtualization there
	const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
</script>

<div
	role="listitem"
	class="flex flex-col justify-between px-3.5 mb-3 w-full {($settings?.widescreenMode ?? null)
		? 'max-w-full'
		: 'max-w-[58rem]'} mx-auto rounded-lg group {isSafari ? '' : 'message-listitem'}"
	class:message-in={(history.messages[messageId]?.timestamp ?? 0) >= OPENED_AT}
>
	{#if history.messages[messageId]}
		{#if history.messages[messageId].role === 'user'}
			<UserMessage
				{user}
				{chatId}
				{history}
				{messageId}
				isFirstMessage={idx === 0}
				siblings={history.messages[messageId].parentId !== null
					? (history.messages[history.messages[messageId].parentId]?.childrenIds ?? [])
					: (Object.values(history.messages)
							.filter((message) => message.parentId === null)
							.map((message) => message.id) ?? [])}
				{gotoMessage}
				{showPreviousMessage}
				{showNextMessage}
				{editMessage}
				{deleteMessage}
				{allowDelete}
				{readOnly}
				{compactPreview}
				{editCodeBlock}
				{topPadding}
				{onInsertToNote}
			/>
		{:else if (history.messages[history.messages[messageId].parentId]?.models?.length ?? 1) === 1}
			<ResponseMessage
				{chatId}
				{history}
				{messageId}
				{selectedModels}
				isLastMessage={messageId === history.currentId}
				siblings={history.messages[history.messages[messageId].parentId]?.childrenIds ?? []}
				{setInputText}
				{gotoMessage}
				{showPreviousMessage}
				{showNextMessage}
				{updateChat}
				{editMessage}
				{saveMessage}
				{rateMessage}
				{actionMessage}
				{submitMessage}
				{deleteMessage}
				{allowDelete}
				{continueResponse}
				{regenerateResponse}
				{addMessages}
				{onToolCallResolved}
				{forkHandler}
				{readOnly}
				{compactPreview}
				{editCodeBlock}
				{topPadding}
			/>
		{:else}
			{#key messageId}
				<MultiResponseMessages
					bind:history
					{chatId}
					{messageId}
					{selectedModels}
					isLastMessage={messageId === history?.currentId}
					{setInputText}
					{updateChat}
					{editMessage}
					{saveMessage}
					{rateMessage}
					{actionMessage}
					{submitMessage}
					{deleteMessage}
					{allowDelete}
					{continueResponse}
					{regenerateResponse}
					{mergeResponses}
					{triggerScroll}
					{addMessages}
					{onToolCallResolved}
					{forkHandler}
					{readOnly}
					{compactPreview}
					{editCodeBlock}
					{topPadding}
					{onInsertToNote}
				/>
			{/key}
		{/if}
	{/if}
</div>

<style>
	/* Browser-native virtualization: skip rendering of off-screen messages
	   without destroying their component trees. Replaces the JS-based
	   culling that caused catastrophic mount/destroy thrashing. */
	.message-listitem {
		content-visibility: auto;
		contain-intrinsic-size: auto 150px;
	}
	/* The newest two messages are always on screen, so skipping them saves
	   nothing - and a message that has never rendered is laid out at the 150px
	   placeholder first. A new "hi" (68px) pushed the reply 82px down for a
	   frame, then it snapped up: the answer's orb visibly jumped on every send.
	   Older messages keep the virtualization and remember their real size. */
	.message-listitem:nth-last-child(-n + 2) {
		content-visibility: visible;
	}

	/* A message sent or received now settles in from just below. */
	.message-in {
		animation: message-in 320ms cubic-bezier(0.2, 0.7, 0.2, 1) backwards;
	}
	@keyframes message-in {
		from {
			opacity: 0;
			translate: 0 6px;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.message-in {
			animation: none;
		}
	}
</style>
