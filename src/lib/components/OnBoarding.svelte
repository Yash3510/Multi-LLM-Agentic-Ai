<script>
	import { getContext } from 'svelte';
	import { WEBUI_NAME } from '$lib/stores';
	const i18n = getContext('i18n');

	export let show = true;
	export let getStartedHandler = () => {};

	// A still image rather than the upstream background video: it cannot fail to
	// autoplay, it is a few hundred KB instead of ~2 MB, and it costs nothing on
	// a machine that is about to spend its GPU on local inference.
	const background = '/assets/onboarding-4ce.webp';
</script>

{#if show}
	<div class="relative h-screen max-h-[100dvh] w-full overflow-hidden text-white">
		<div class="fixed top-6 left-6 z-50 sm:top-10 sm:left-10">
			<!-- LICENSE covers this Open WebUI onboarding logo.
			Do not alter, remove, obscure, or replace it except as LICENSE permits:
			https://docs.openwebui.com/license. -->
			<img
				id="logo"
				crossorigin="anonymous"
				src="/static/favicon.png"
				class="size-6 rounded-full"
				alt="logo"
			/>
		</div>

		<img
			class="absolute inset-0 h-full w-full object-cover"
			src={background}
			alt=""
			aria-hidden="true"
		/>

		<div class="absolute inset-0 bg-linear-to-t from-black/80 via-black/20 to-transparent"></div>
		<div class="absolute inset-0 bg-linear-to-r from-black/50 via-black/10 to-transparent"></div>

		<div class="relative z-10 flex h-screen max-h-[100dvh] w-full">
			<div class="flex w-full flex-col justify-end px-6 pb-8 sm:px-10 sm:pb-10 lg:px-16 lg:pb-14">
				<div class="max-w-3xl">
					<!-- LICENSE covers this Open WebUI welcome identifier.
					Do not alter, remove, obscure, or replace it except as LICENSE permits:
					https://docs.openwebui.com/license. -->
					<div class="mb-4 text-[0.6875rem] font-medium tracking-[0.18em] uppercase opacity-35">
						{$WEBUI_NAME}
					</div>

					<h1 class="m-0 max-w-3xl text-2xl leading-[1.15] font-light tracking-tight lg:text-4xl">
						{$i18n.t('Confidential work never leaves the premises.')}
					</h1>

					<p class="mt-6 max-w-xl text-sm leading-relaxed font-light text-white/60 lg:text-base">
						{$i18n.t(
							'A sovereign agentic workbench for the knowledge work a plant cannot send to a cloud assistant. Inspection reports, approval notes, engineering calculations and internal code, handled by open-weight models running on your own hardware. Every task is planned, grounded in your own manuals, verified, and released only once a person approves it.'
						)}
					</p>

					<div class="mt-8 flex flex-col items-start gap-6 sm:flex-row sm:items-center sm:gap-7">
						<button
							aria-label={$i18n.t('Get started')}
							class="group relative z-20 inline-flex min-w-40 items-center justify-center gap-2 bg-white px-8 py-3 text-sm font-normal text-black transition hover:bg-white/90 focus:ring-2 focus:ring-white/50 focus:outline-hidden"
							on:click={() => {
								getStartedHandler();
							}}
						>
							{$i18n.t('Get started')}
							<svg
								class="h-4 w-4 transition group-hover:translate-x-0.5"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
								stroke-width="1.5"
								aria-hidden="true"
							>
								<path stroke-linecap="round" stroke-linejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
							</svg>
						</button>

						<!-- No outbound link here by design: the first screen of an
						air-gapped workbench should not point off the machine. -->
						<div class="text-xs leading-relaxed font-light text-white/40">
							{$i18n.t('Local open-weight models')}
							<span class="mx-2 text-white/20">·</span>
							{$i18n.t('No external connections')}
							<span class="mx-2 text-white/20">·</span>
							{$i18n.t('Every action audited')}
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}
