<script lang="ts">
	import DOMPurify from 'dompurify';
	import { marked } from 'marked';

	import { toast } from 'svelte-sonner';

	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	import { getBackendConfig } from '$lib/apis';
	import {
		ldapUserSignIn,
		getSessionUser,
		userSignIn,
		userSignUp,
		updateUserTimezone
	} from '$lib/apis/auths';

	import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';
	import { WEBUI_NAME, config, user, socket } from '$lib/stores';

	import { generateInitialsImage, canvasPixelTest, getUserTimezone } from '$lib/utils';

	import Spinner from '$lib/components/common/Spinner.svelte';
	import OnBoarding from '$lib/components/OnBoarding.svelte';
	import AuthField from '$lib/components/auth/AuthField.svelte';
	import { redirect } from '@sveltejs/kit';

	const i18n = getContext('i18n');

	let loaded = false;

	let mode = $config?.features.enable_ldap ? 'ldap' : 'signin';

	let form = null;

	let name = '';
	let email = '';
	let password = '';
	let confirmPassword = '';

	let ldapUsername = '';

	let submitting = false;

	/* What went wrong, said under the fields rather than in a toast, and the
	   field it is about. Cleared as soon as you type again. */
	let formError = '';
	let badField = '';
	let caps = false;
	let emailInput;
	let passwordInput;
	let usernameInput;
	let nameInput;
	$: name, email, password, confirmPassword, ldapUsername, (formError = ''), (badField = '');

	const say = (message, field = '') => {
		formError = message;
		badField = field;
		const input = { email: emailInput, password: passwordInput, username: usernameInput, name: nameInput }[field];
		if (input) {
			input.focus();
			if (field === 'password') input.select();
		}
	};
	/* The server's words for a wrong password are long and generic; say it
	   plainly. Anything else is shown as the server put it. */
	const refused = (error, field = 'password') => {
		const text = `${error ?? ''}`.trim();
		if (/incorrect|invalid|typos|credentials/i.test(text)) {
			say(
				mode === 'ldap'
					? $i18n.t("That username and password don't match.")
					: $i18n.t("That email and password don't match."),
				field
			);
		} else {
			say(text || $i18n.t('Something went wrong. Try again.'), '');
		}
	};

	const setSessionUser = async (sessionUser, redirectPath: string | null = null) => {
		if (sessionUser) {
			if (sessionUser.token) {
				localStorage.token = sessionUser.token;
			}
			$socket.emit('user-join', { auth: { token: sessionUser.token } });
			await user.set(sessionUser);
			await config.set(await getBackendConfig());

			// Update user timezone
			const timezone = getUserTimezone();
			if (sessionUser.token && timezone) {
				updateUserTimezone(sessionUser.token, timezone);
			}

			if (!redirectPath) {
				redirectPath = $page.url.searchParams.get('redirect') || '/';
			}

			// Signing in stays inside the app, so the 4CE intro (static/4ce-intro.js)
			// would not otherwise run; it covers the switch into the chat.
			(window as any).__fourceIntro?.play();
			goto(redirectPath);
			localStorage.removeItem('redirectPath');
		}
	};

	const signInHandler = async () => {
		const sessionUser = await userSignIn(email, password).catch((error) => {
			refused(error);
			return null;
		});

		await setSessionUser(sessionUser);
	};

	const signUpHandler = async () => {
		if ($config?.features?.enable_signup_password_confirmation) {
			if (password !== confirmPassword) {
				say($i18n.t("The passwords don't match."), 'password');
				return;
			}
		}

		const sessionUser = await userSignUp(name, email, password, generateInitialsImage(name)).catch(
			(error) => {
				say(`${error ?? ''}`.trim() || $i18n.t('Something went wrong. Try again.'));
				return null;
			}
		);

		await setSessionUser(sessionUser);
	};

	const ldapSignInHandler = async () => {
		const sessionUser = await ldapUserSignIn(ldapUsername, password).catch((error) => {
			refused(error);
			return null;
		});
		await setSessionUser(sessionUser);
	};

	const submitHandler = async () => {
		if (submitting) {
			return;
		}
		// Say what is missing before asking the server.
		if (mode === 'signup' && !name.trim()) return say($i18n.t('Enter your name.'), 'name');
		if (mode === 'ldap' && !ldapUsername.trim()) return say($i18n.t('Enter your username.'), 'username');
		if (mode !== 'ldap' && !email.trim()) return say($i18n.t('Enter your email.'), 'email');
		if (!password) return say($i18n.t('Enter your password.'), 'password');

		submitting = true;
		try {
			if (mode === 'ldap') {
				await ldapSignInHandler();
			} else if (mode === 'signin') {
				await signInHandler();
			} else {
				await signUpHandler();
			}
		} finally {
			submitting = false;
		}
	};

	const oauthCallbackHandler = async () => {
		// Get the value of the 'token' cookie
		function getCookie(name) {
			const match = document.cookie.match(
				new RegExp('(?:^|; )' + name.replace(/([.$?*|{}()[\]\\/+^])/g, '\\$1') + '=([^;]*)')
			);
			return match ? decodeURIComponent(match[1]) : null;
		}

		const token = getCookie('token');
		if (!token) {
			return;
		}

		const sessionUser = await getSessionUser(token).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		if (!sessionUser) {
			return;
		}

		localStorage.token = token;
		await setSessionUser(sessionUser, localStorage.getItem('redirectPath') || null);
	};

	let onboarding = false;

	onMount(async () => {
		const redirectPath = $page.url.searchParams.get('redirect');
		const logout = $page.url.searchParams.get('state') === 'logout';

		if ($user && !logout) {
			goto(redirectPath || '/');
		} else {
			if (redirectPath) {
				localStorage.setItem('redirectPath', redirectPath);
			}
		}

		const error = $page.url.searchParams.get('error');
		if (error) {
			formError = error;
		}

		await oauthCallbackHandler();
		form = $page.url.searchParams.get('form');

		// Auto-redirect to SSO when OAUTH_AUTO_REDIRECT is enabled and the
		// deployment is unambiguously SSO-only (single provider, no login form,
		// no LDAP). Suppressed after logout, by ?form=, ?error=, onboarding,
		// trusted-header auth, or an existing session/token.
		if ($config?.oauth?.auto_redirect && !logout && !form && !error) {
			const providers = Object.keys($config?.oauth?.providers ?? {});
			if (
				providers.length === 1 &&
				$config?.features?.auth !== false &&
				$config?.features?.enable_login_form === false &&
				!$config?.features?.enable_ldap &&
				!$config?.features?.auth_trusted_header &&
				!$config?.onboarding &&
				!localStorage.token &&
				!document.cookie.split('; ').some((c) => c.startsWith('token='))
			) {
				window.location.href = `${WEBUI_BASE_URL}/oauth/${providers[0]}/login`;
				return;
			}
		}

		loaded = true;
		setTimeout(() => (mode === 'ldap' ? usernameInput : emailInput)?.focus(), 60);

		if (($config?.features?.auth_trusted_header ?? false) || $config?.features?.auth === false) {
			await signInHandler();
		} else {
			onboarding = $config?.onboarding ?? false;
		}
	});
</script>

<svelte:head>
	<!-- LICENSE covers this Open WebUI browser-title identifier.
	Do not alter, remove, obscure, or replace it except as LICENSE permits:
	https://docs.openwebui.com/license. -->
	<title>
		{`${$WEBUI_NAME}`}
	</title>
</svelte:head>

<OnBoarding
	bind:show={onboarding}
	getStartedHandler={() => {
		onboarding = false;
		mode = $config?.features.enable_ldap ? 'ldap' : 'signup';
	}}
/>

<div class="w-full h-screen max-h-[100dvh] text-white relative" id="auth-page">
	<div class="w-full h-full absolute top-0 left-0 bg-white dark:bg-black"></div>

	<div class="w-full absolute top-0 left-0 right-0 h-8 drag-region" />

	{#if loaded}
		<div
			class="fixed bg-transparent min-h-screen w-full flex justify-center z-50 text-black dark:text-white"
			id="auth-container"
		>
			<div class="w-full px-10 min-h-screen flex flex-col text-center">
				{#if ($config?.features.auth_trusted_header ?? false) || $config?.features.auth === false}
					<div class=" my-auto pb-10 w-full sm:max-w-md">
						<div
							class="flex items-center justify-center gap-3 text-xl sm:text-2xl text-center font-normal dark:text-gray-200"
						>
							<div>
								{$i18n.t('Signing in to {{WEBUI_NAME}}', { WEBUI_NAME: $WEBUI_NAME })}
							</div>

							<div>
								<Spinner className="size-5" />
							</div>
						</div>
					</div>
				{:else}
					<div class="my-auto flex flex-col justify-center items-center">
						<div id="auth-login-card" class="my-auto w-full max-w-[21.5rem] pb-10 dark:text-gray-100">
							{#if $config?.metadata?.auth_logo_position === 'center'}
								<div class="flex justify-center mb-6">
									<!-- LICENSE covers this Open WebUI sign-in logo.
									Do not alter, remove, obscure, or replace it except as LICENSE permits:
									https://docs.openwebui.com/license. -->
									<img
										id="logo"
										crossorigin="anonymous"
										src="{WEBUI_BASE_URL}/static/favicon.png"
										class="size-24"
										alt="{$WEBUI_NAME} logo"
									/>
								</div>
							{/if}
							<form
								class="flex flex-col text-left"
								novalidate
								on:submit={(e) => {
									e.preventDefault();
									submitHandler();
								}}
							>
								<h1 class="mb-6 text-[26px] font-medium leading-tight tracking-[-0.01em] text-gray-900 dark:text-gray-50">
									{#if $config?.onboarding ?? false}
										{$i18n.t(`Get started with {{WEBUI_NAME}}`, { WEBUI_NAME: $WEBUI_NAME })}
									{:else if mode === 'ldap'}
										{$i18n.t(`Sign in to {{WEBUI_NAME}} with LDAP`, { WEBUI_NAME: $WEBUI_NAME })}
									{:else if mode === 'signin'}
										{$i18n.t(`Sign in to {{WEBUI_NAME}}`, { WEBUI_NAME: $WEBUI_NAME })}
									{:else}
										{$i18n.t(`Create your {{WEBUI_NAME}} account`, { WEBUI_NAME: $WEBUI_NAME })}
									{/if}
								</h1>

								{#if $config?.onboarding ?? false}
									<p class="-mt-3 mb-5 text-[13px] leading-relaxed text-gray-600 dark:text-gray-400">
										{$i18n.t('This first account is the admin. Everything stays on this machine.')}
									</p>
								{/if}

								{#if $config?.features.enable_login_form || $config?.features.enable_ldap || form}
									<div class="flex flex-col gap-2.5">
										{#if mode === 'signup'}
											<AuthField
												id="name"
												name="name"
												label={$i18n.t('Name')}
												autocomplete="name"
												invalid={badField === 'name'}
												bind:value={name}
												bind:input={nameInput}
											/>
										{/if}

										{#if mode === 'ldap'}
											<AuthField
												id="username"
												name="username"
												label={$i18n.t('Username')}
												autocomplete="username"
												invalid={badField === 'username'}
												bind:value={ldapUsername}
												bind:input={usernameInput}
											/>
										{:else}
											<AuthField
												id="email"
												name="email"
												type="email"
												label={$i18n.t('Email')}
												autocomplete="email"
												invalid={badField === 'email'}
												bind:value={email}
												bind:input={emailInput}
											/>
										{/if}

										<AuthField
											id="password"
											name="password"
											type="password"
											label={$i18n.t('Password')}
											autocomplete={mode === 'signup' ? 'new-password' : 'current-password'}
											invalid={badField === 'password'}
											bind:value={password}
											bind:input={passwordInput}
											bind:caps
										/>

										{#if mode === 'signup' && $config?.features?.enable_signup_password_confirmation}
											<AuthField
												id="confirm-password"
												name="confirm-password"
												type="password"
												label={$i18n.t('Confirm password')}
												autocomplete="new-password"
												bind:value={confirmPassword}
											/>
										{/if}
									</div>

									<!-- Notes under the fields: open and close in place, so the
									     button below moves smoothly rather than jumping. -->
									<div class="auth-note" class:open={caps && !formError}>
										<p class="flex items-center gap-1.5 pt-2.5 text-[12.5px] text-gray-600 dark:text-gray-400">
											<svg class="size-[15px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" aria-hidden="true"><path d="M12 4 4 12h4v6h8v-6h4Z" /></svg>
											{$i18n.t('Caps Lock is on')}
										</p>
									</div>
									<div class="auth-note" class:open={!!formError} role="alert">
										<p class="flex items-start gap-1.5 pt-2.5 text-[12.5px] leading-snug text-red-700 dark:text-red-300">
											<svg class="mt-px size-[15px] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7.5v5.5M12 16.5v.01" /></svg>
											<span>{formError}</span>
										</p>
									</div>

									<button
										class="auth-go relative mt-4 flex h-[46px] w-full items-center justify-center overflow-hidden rounded-full bg-gray-900 text-[14.5px] font-medium text-white transition hover:bg-gray-800 active:scale-[0.99] disabled:cursor-default dark:bg-white dark:text-gray-900 dark:hover:bg-gray-100"
										type="submit"
										disabled={submitting}
									>
										<span class="auth-go-label" class:away={submitting}>
											{mode === 'ldap'
												? $i18n.t('Authenticate')
												: mode === 'signin'
													? $i18n.t('Sign in')
													: ($config?.onboarding ?? false)
														? $i18n.t('Create admin account')
														: $i18n.t('Create account')}
										</span>
										<!-- Working: the rail's six dots, while the server checks. -->
										<span class="auth-go-busy" class:here={submitting} aria-hidden={!submitting}>
											<svg class="auth-dots size-3.5" viewBox="0 0 14 14" aria-hidden="true">
												{#each [0, 1, 2, 3, 4, 5] as i}
													<circle
														cx={7 + 5.2 * Math.cos(((-90 + 60 * i) * Math.PI) / 180)}
														cy={7 + 5.2 * Math.sin(((-90 + 60 * i) * Math.PI) / 180)}
														r="1.2"
														style="animation-delay: {((i * 1.7) / 6).toFixed(2)}s"
													/>
												{/each}
												<circle class="hub" cx="7" cy="7" r="1" />
											</svg>
											{mode === 'signup' ? $i18n.t('Creating your account') : $i18n.t('Signing in')}
										</span>
									</button>

									{#if mode === 'signin'}
										<p class="mt-3 text-center text-[12px] text-gray-500 dark:text-gray-400">
											{$i18n.t('Forgot your password? Your admin can reset it.')}
										</p>
									{/if}

									{#if $config?.features.enable_signup && !($config?.onboarding ?? false) && mode !== 'ldap'}
										<p class="mt-5 text-center text-[13px] text-gray-600 dark:text-gray-400">
											{mode === 'signin' ? $i18n.t('New here?') : $i18n.t('Already have an account?')}
											<button
												class="auth-link"
												type="button"
												on:click={() => {
													mode = mode === 'signin' ? 'signup' : 'signin';
													formError = '';
												}}
											>
												{mode === 'signin' ? $i18n.t('Create an account') : $i18n.t('Sign in')}
											</button>
										</p>
									{/if}
								{/if}
							</form>

							{#if Object.keys($config?.oauth?.providers ?? {}).length > 0}
								<div class="my-5 flex w-full items-center gap-3">
									<hr class="h-px flex-1 border-0 bg-gray-200 dark:bg-gray-800" />
									{#if $config?.features.enable_login_form || $config?.features.enable_ldap || form}
										<span class="text-[12px] text-gray-500 dark:text-gray-400">{$i18n.t('or')}</span>
									{/if}

									<hr class="h-px flex-1 border-0 bg-gray-200 dark:bg-gray-800" />
								</div>
								<div class="flex flex-col gap-2">
									{#if $config?.oauth?.providers?.google}
										<button
											class="flex h-[46px] w-full items-center justify-center rounded-full border border-gray-200 text-[14px] font-medium text-gray-800 transition hover:border-gray-300 hover:bg-gray-50 dark:border-gray-800 dark:text-gray-200 dark:hover:border-gray-700 dark:hover:bg-gray-900"
											on:click={() => {
												window.location.href = `${WEBUI_BASE_URL}/oauth/google/login`;
											}}
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												viewBox="0 0 48 48"
												class="size-6 mr-3"
												aria-hidden="true"
											>
												<path
													fill="#EA4335"
													d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"
												/><path
													fill="#4285F4"
													d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
												/><path
													fill="#FBBC05"
													d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"
												/><path
													fill="#34A853"
													d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"
												/><path fill="none" d="M0 0h48v48H0z" />
											</svg>
											<span>{$i18n.t('Continue with {{provider}}', { provider: 'Google' })}</span>
										</button>
									{/if}
									{#if $config?.oauth?.providers?.microsoft}
										<button
											class="flex h-[46px] w-full items-center justify-center rounded-full border border-gray-200 text-[14px] font-medium text-gray-800 transition hover:border-gray-300 hover:bg-gray-50 dark:border-gray-800 dark:text-gray-200 dark:hover:border-gray-700 dark:hover:bg-gray-900"
											on:click={() => {
												window.location.href = `${WEBUI_BASE_URL}/oauth/microsoft/login`;
											}}
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												viewBox="0 0 21 21"
												class="size-6 mr-3"
												aria-hidden="true"
											>
												<rect x="1" y="1" width="9" height="9" fill="#f25022" /><rect
													x="1"
													y="11"
													width="9"
													height="9"
													fill="#00a4ef"
												/><rect x="11" y="1" width="9" height="9" fill="#7fba00" /><rect
													x="11"
													y="11"
													width="9"
													height="9"
													fill="#ffb900"
												/>
											</svg>
											<span>{$i18n.t('Continue with {{provider}}', { provider: 'Microsoft' })}</span
											>
										</button>
									{/if}
									{#if $config?.oauth?.providers?.github}
										<button
											class="flex h-[46px] w-full items-center justify-center rounded-full border border-gray-200 text-[14px] font-medium text-gray-800 transition hover:border-gray-300 hover:bg-gray-50 dark:border-gray-800 dark:text-gray-200 dark:hover:border-gray-700 dark:hover:bg-gray-900"
											on:click={() => {
												window.location.href = `${WEBUI_BASE_URL}/oauth/github/login`;
											}}
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												viewBox="0 0 24 24"
												class="size-6 mr-3"
												aria-hidden="true"
											>
												<path
													fill="currentColor"
													d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.92 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57C20.565 21.795 24 17.31 24 12c0-6.63-5.37-12-12-12z"
												/>
											</svg>
											<span>{$i18n.t('Continue with {{provider}}', { provider: 'GitHub' })}</span>
										</button>
									{/if}
									{#if $config?.oauth?.providers?.oidc}
										<button
											class="flex h-[46px] w-full items-center justify-center rounded-full border border-gray-200 text-[14px] font-medium text-gray-800 transition hover:border-gray-300 hover:bg-gray-50 dark:border-gray-800 dark:text-gray-200 dark:hover:border-gray-700 dark:hover:bg-gray-900"
											on:click={() => {
												window.location.href = `${WEBUI_BASE_URL}/oauth/oidc/login`;
											}}
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												fill="none"
												viewBox="0 0 24 24"
												stroke-width="1.5"
												stroke="currentColor"
												class="size-6 mr-3"
												aria-hidden="true"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1 1 21.75 8.25Z"
												/>
											</svg>

											<span
												>{$i18n.t('Continue with {{provider}}', {
													provider: $config?.oauth?.providers?.oidc ?? 'SSO'
												})}</span
											>
										</button>
									{/if}
									{#if $config?.oauth?.providers?.feishu}
										<button
											class="flex h-[46px] w-full items-center justify-center rounded-full border border-gray-200 text-[14px] font-medium text-gray-800 transition hover:border-gray-300 hover:bg-gray-50 dark:border-gray-800 dark:text-gray-200 dark:hover:border-gray-700 dark:hover:bg-gray-900"
											on:click={() => {
												window.location.href = `${WEBUI_BASE_URL}/oauth/feishu/login`;
											}}
										>
											<span>{$i18n.t('Continue with {{provider}}', { provider: 'Feishu' })}</span>
										</button>
									{/if}
								</div>
							{/if}

							{#if $config?.features.enable_ldap && $config?.features.enable_login_form}
								<div class="mt-4">
									<button
										class="auth-link mx-auto flex text-[13px] text-gray-600 dark:text-gray-400"
										type="button"
										on:click={() => {
											if (mode === 'ldap')
												mode = ($config?.onboarding ?? false) ? 'signup' : 'signin';
											else mode = 'ldap';
										}}
									>
										<span
											>{mode === 'ldap'
												? $i18n.t('Continue with Email')
												: $i18n.t('Continue with LDAP')}</span
										>
									</button>
								</div>
							{/if}
						</div>
						{#if $config?.metadata?.login_footer}
							<div class="max-w-3xl mx-auto">
								<div class="mt-2 text-[0.7rem] text-gray-500 dark:text-gray-400 marked">
									{@html DOMPurify.sanitize(marked($config?.metadata?.login_footer))}
								</div>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		</div>

		{#if !$config?.metadata?.auth_logo_position}
			<div class="fixed m-10 z-50">
				<div class="flex space-x-2">
					<div class=" self-center">
						<!-- LICENSE covers this Open WebUI sign-in logo.
						Do not alter, remove, obscure, or replace it except as LICENSE permits:
						https://docs.openwebui.com/license. -->
						<span id="logo" class="inline-flex">
							<img
								crossorigin="anonymous"
								src="{WEBUI_BASE_URL}/static/logo-mark-dark.svg"
								class="size-6 dark:hidden"
								alt=""
							/>
							<img
								crossorigin="anonymous"
								src="{WEBUI_BASE_URL}/static/logo-mark-light.svg"
								class="size-6 hidden dark:block"
								alt=""
							/>
						</span>
					</div>
				</div>
			</div>
		{/if}
	{/if}
</div>

<style>
	/* A note under the fields opens and closes in place (a grid row from 0
	   to its height), so what is below it slides rather than jumps. */
	.auth-note {
		display: grid;
		grid-template-rows: 0fr;
		opacity: 0;
		transition:
			grid-template-rows 300ms cubic-bezier(0.22, 1, 0.36, 1),
			opacity 220ms ease;
	}
	.auth-note > * {
		overflow: hidden;
	}
	.auth-note.open {
		grid-template-rows: 1fr;
		opacity: 1;
	}

	/* The button's label gives way to the working dots, and back. */
	.auth-go-label,
	.auth-go-busy {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		transition:
			opacity 280ms ease,
			transform 400ms cubic-bezier(0.22, 1, 0.36, 1);
	}
	.auth-go-label.away {
		opacity: 0;
		transform: translateY(-6px);
	}
	.auth-go-busy {
		opacity: 0;
		transform: translateY(6px);
	}
	.auth-go-busy.here {
		opacity: 1;
		transform: none;
	}
	.auth-dots circle {
		fill: #c4b5fd;
		opacity: 0.35;
		animation: auth-dot 1.7s ease-in-out infinite;
	}
	.auth-dots .hub {
		opacity: 1;
		animation: none;
	}
	:global(.dark) .auth-dots circle {
		fill: #7c3aed;
	}
	@keyframes auth-dot {
		0% {
			opacity: 1;
		}
		35% {
			opacity: 0.7;
		}
		70%,
		100% {
			opacity: 0.35;
		}
	}

	.auth-link {
		color: var(--color-gray-900, #1c1c1c);
		text-decoration: underline;
		text-decoration-color: var(--color-gray-300, #cdcdcd);
		text-underline-offset: 3px;
		transition: text-decoration-color 200ms ease;
	}
	.auth-link:hover {
		text-decoration-color: currentColor;
	}
	:global(.dark) .auth-link {
		color: #fff;
		text-decoration-color: var(--color-gray-700, #525252);
	}

	@media (prefers-reduced-motion: reduce) {
		.auth-note,
		.auth-go-label,
		.auth-go-busy {
			transition: none;
		}
		.auth-dots circle {
			animation: none;
			opacity: 0.8;
		}
	}
</style>
