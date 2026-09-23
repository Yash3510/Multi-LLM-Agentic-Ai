<script>
	/*
	 * AuthField - one field of the sign-in page: the label sits inside the
	 * field and floats up as it is focused or filled, a password field has an
	 * eye to show what was typed, and it reports Caps Lock while you type in
	 * it. The label floats by CSS, so a value the browser autofills (which
	 * scripts cannot read until you interact) never sits under it.
	 */
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	export let id;
	export let label;
	export let type = 'text';
	export let value = '';
	export let name = undefined;
	export let autocomplete = 'off';
	export let invalid = false;
	/** Caps Lock, while typing in a password field. */
	export let caps = false;
	export let input = null;

	let show = false;
	$: kind = type === 'password' && show ? 'text' : type;

	const onKey = (e) => {
		if (type === 'password' && e.getModifierState) caps = e.getModifierState('CapsLock');
	};
</script>

<div class="auth-field relative" class:invalid>
	<input
		bind:this={input}
		{id}
		{name}
		{autocomplete}
		type={kind}
		{value}
		placeholder=" "
		spellcheck="false"
		aria-invalid={invalid}
		class="peer h-[52px] w-full rounded-2xl border border-gray-200 bg-gray-50/70 px-3.5 pb-1.5 pt-5 text-[15px] text-gray-900 outline-none transition-[border-color,background-color,box-shadow] duration-200 focus:border-gray-900 focus:bg-white focus:ring-4 focus:ring-gray-900/[0.06] dark:border-gray-800 dark:bg-gray-900/60 dark:text-gray-100 dark:focus:border-gray-300 dark:focus:bg-gray-900 dark:focus:ring-white/[0.07] {type ===
		'password'
			? 'pr-12'
			: ''}"
		on:input={(e) => (value = e.currentTarget.value)}
		on:keydown={onKey}
		on:keyup={onKey}
		on:blur={() => (caps = false)}
	/>
	<label for={id}>{label}</label>
	{#if type === 'password'}
		<button
			type="button"
			class="absolute right-2 top-[9px] flex size-[34px] items-center justify-center rounded-xl text-gray-500 transition hover:bg-gray-900/[0.05] hover:text-gray-900 dark:text-gray-400 dark:hover:bg-white/[0.07] dark:hover:text-white"
			aria-pressed={show}
			aria-label={show ? $i18n.t('Hide password') : $i18n.t('Show password')}
			on:click={() => {
				show = !show;
				input?.focus();
			}}
		>
			<svg
				class="size-[18px]"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="1.6"
				stroke-linecap="round"
				stroke-linejoin="round"
				aria-hidden="true"
			>
				{#if show}
					<path d="M10.6 10.6a2 2 0 0 0 2.8 2.8" />
					<path d="M9.4 5.2A9.6 9.6 0 0 1 12 5c4.5 0 8 3.3 9.5 7a11 11 0 0 1-2.6 3.8M6.6 6.6A11 11 0 0 0 2.5 12c1.5 3.7 5 7 9.5 7a9.4 9.4 0 0 0 5.4-1.6" />
					<path d="M3 3l18 18" />
				{:else}
					<path d="M2.5 12c1.5-3.7 5-7 9.5-7s8 3.3 9.5 7c-1.5 3.7-5 7-9.5 7s-8-3.3-9.5-7Z" />
					<circle cx="12" cy="12" r="2.6" />
				{/if}
			</svg>
		</button>
	{/if}
</div>

<style>
	label {
		position: absolute;
		left: 15px;
		top: 15px;
		font-size: 15px;
		line-height: 1.4;
		color: var(--color-gray-500, #9b9b9b);
		pointer-events: none;
		transform-origin: left top;
		transition:
			transform 200ms cubic-bezier(0.22, 1, 0.36, 1),
			color 200ms ease;
	}
	/* Focused, filled or autofilled: the label rests above the text. */
	input:focus + label,
	input:not(:placeholder-shown) + label,
	input:-webkit-autofill + label {
		transform: translateY(-9px) scale(0.76);
		color: var(--color-gray-600, #676767);
	}
	:global(.dark) input:focus + label,
	:global(.dark) input:not(:placeholder-shown) + label,
	:global(.dark) input:-webkit-autofill + label {
		color: var(--color-gray-400, #b4b4b4);
	}
	.invalid input {
		border-color: #fca5a5;
	}
	.invalid input:focus {
		border-color: #f87171;
		box-shadow: 0 0 0 4px rgb(248 113 113 / 0.15);
	}
	:global(.dark) .invalid input {
		border-color: rgb(248 113 113 / 0.5);
	}
	/* Autofill. The browser paints a filled-in field its own way: it forces
	   the text to its field colour (black unless told the page is dark) and
	   tints the background. On the dark page that left black text on a dark
	   field. The text colour is set outright, the field is told which scheme
	   it is in, and the tint is held off so the field keeps its own colour. */
	input {
		caret-color: var(--color-gray-900, #1c1c1c);
	}
	:global(.dark) input {
		color-scheme: dark;
		caret-color: #fff;
	}
	input:-webkit-autofill,
	input:-webkit-autofill:hover,
	input:-webkit-autofill:focus {
		-webkit-text-fill-color: var(--color-gray-900, #1c1c1c);
		transition:
			background-color 600000s 0s,
			color 600000s 0s;
	}
	:global(.dark) input:-webkit-autofill,
	:global(.dark) input:-webkit-autofill:hover,
	:global(.dark) input:-webkit-autofill:focus {
		-webkit-text-fill-color: var(--color-gray-100, #efefef);
	}
</style>
