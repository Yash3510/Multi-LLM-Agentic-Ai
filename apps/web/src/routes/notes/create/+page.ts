import { redirect } from '@sveltejs/kit';
import { data } from '$lib/data';

// A new note opens straight in the editor.
export const load = async () => {
  const note = await data.createNote({ title: '', content: '' });
  redirect(307, `/notes/${note.id}`);
};
