<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { WEBUI_NAME, showSidebar, mobile, user } from '$lib/stores';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';
	import Sovereignty from '$lib/components/fource/Sovereignty.svelte';

	const i18n = getContext('i18n');

	// 4CE: the page names processes, ports and addresses on this machine.
	onMount(() => {
		if ($user?.role !== 'admin') {
			goto('/');
		}
	});
</script>

<svelte:head>
	<!-- LICENSE covers this Open WebUI browser-title identifier.
	Do not alter, remove, obscure, or replace it except as LICENSE permits:
	https://docs.openwebui.com/license. -->
	<title>
		{$i18n.t('Sovereignty')} / {$WEBUI_NAME}
	</title>
</svelte:head>

<div
	class="flex flex-col w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
		? 'md:max-w-[calc(100%-var(--sidebar-width))]'
		: ''} max-w-full"
>
	<nav class="pb-1 px-2.5 pt-2 backdrop-blur-xl drag-region select-none">
		<div class="flex items-center gap-0.5 md:gap-1">
			{#if $mobile || !$showSidebar}
				<div class="self-center flex flex-none items-center">
					<Tooltip
						content={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
						interactive={true}
					>
						<button
							id="sidebar-toggle-button"
							class="cursor-pointer flex rounded-lg hover:bg-gray-100 dark:hover:bg-gray-850 transition"
							aria-label={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
							on:click={() => {
								showSidebar.set(!$showSidebar);
							}}
						>
							<div class="self-center p-1.5">
								<Sidebar className="size-4" />
							</div>
						</button>
					</Tooltip>
				</div>
			{/if}
		</div>
	</nav>

	<div class="flex-1 overflow-y-auto">
		{#if $user?.role === 'admin'}
			<Sovereignty />
		{/if}
	</div>
</div>
