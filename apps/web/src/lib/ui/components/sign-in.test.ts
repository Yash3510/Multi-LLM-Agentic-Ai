import { fireEvent, render } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import SignInForm from './SignInForm.svelte';

const fill = async (field: HTMLElement, value: string) =>
  fireEvent.input(field, { target: { value } });

describe('SignInForm', () => {
  it('names the missing field instead of submitting', async () => {
    const onsubmit = vi.fn();
    const { getByRole, getByLabelText } = render(SignInForm, {
      props: { mode: 'sign-in', product: '4CE', onsubmit },
    });
    await fireEvent.click(getByRole('button', { name: 'Sign in' }));
    expect(getByRole('alert').textContent).toContain('Enter your email.');
    await fill(getByLabelText('Email'), 'asha@example.org');
    await fireEvent.click(getByRole('button', { name: 'Sign in' }));
    expect(getByRole('alert').textContent).toContain('Enter your password.');
    expect(onsubmit).not.toHaveBeenCalled();
  });

  it('hands the values to the caller and never submits to a URL', async () => {
    const onsubmit = vi.fn().mockResolvedValue(undefined);
    const { getByRole, getByLabelText, container } = render(SignInForm, {
      props: { mode: 'sign-in', product: '4CE', onsubmit },
    });
    const form = container.querySelector('form')!;
    expect(form.getAttribute('action')).toBeNull();
    expect(form.getAttribute('method')).toBeNull();
    await fill(getByLabelText('Email'), 'asha@example.org');
    await fill(getByLabelText('Password'), 'secret-123');
    await fireEvent.click(getByRole('button', { name: 'Sign in' }));
    expect(onsubmit).toHaveBeenCalledWith({
      name: '',
      email: 'asha@example.org',
      password: 'secret-123',
    });
    expect(window.location.href).not.toContain('secret-123');
  });

  it('shows the server message when sign-in fails, cleared on typing', async () => {
    const onsubmit = vi.fn().mockRejectedValue(new Error("That email and password don't match."));
    const { getByRole, getByLabelText, queryByRole } = render(SignInForm, {
      props: { mode: 'sign-in', product: '4CE', onsubmit },
    });
    await fill(getByLabelText('Email'), 'asha@example.org');
    await fill(getByLabelText('Password'), 'wrong');
    await fireEvent.click(getByRole('button', { name: 'Sign in' }));
    expect((await vi.waitFor(() => getByRole('alert'))).textContent).toContain("don't match");
    await fill(getByLabelText('Password'), 'wrong2');
    expect(queryByRole('alert')).toBeNull();
  });

  it('shows and hides the password, and notes Caps Lock', async () => {
    const { getByRole, getByLabelText, getByText } = render(SignInForm, {
      props: { mode: 'sign-in', product: '4CE', onsubmit: vi.fn() },
    });
    const password = getByLabelText('Password') as HTMLInputElement;
    expect(password.type).toBe('password');
    await fireEvent.click(getByRole('button', { name: 'Show password' }));
    expect(password.type).toBe('text');
    const note = getByText('Caps Lock is on').closest('.note')!;
    expect(note.hasAttribute('data-open')).toBe(false);
    await fireEvent.keyDown(password, { key: 'A', modifierCapsLock: true });
    expect(note.hasAttribute('data-open')).toBe(true);
  });

  it('asks for a name and makes the admin in first-account mode', () => {
    const { getByRole, getByLabelText } = render(SignInForm, {
      props: { mode: 'first-account', product: '4CE', onsubmit: vi.fn() },
    });
    expect(getByRole('heading', { name: 'Get started with 4CE' })).toBeTruthy();
    expect(getByLabelText('Name')).toBeTruthy();
    expect(getByRole('button', { name: 'Create admin account' })).toBeTruthy();
  });
});
