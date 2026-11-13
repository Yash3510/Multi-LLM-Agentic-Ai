// What a Field tells the control inside it: the ids that wire label, description and error to the
// control, and the states the control must show. Getters, so the control follows the Field's props.
import { getContext, setContext } from 'svelte';
import type { Attachment } from 'svelte/attachments';

export interface FieldContext {
  /** The control's id, which the label points at. Undefined in a group: each control keeps its own. */
  readonly id: string | undefined;
  /** Undefined when the Field has no visible label. */
  readonly labelId: string | undefined;
  /** Description and error ids, for aria-describedby. */
  readonly describedBy: string | undefined;
  /** The label names a set of controls (radios, segments, a checkbox list), not one control. */
  readonly group: boolean;
  readonly invalid: boolean;
  readonly required: boolean;
  readonly disabled: boolean;
  readonly readonly: boolean;
  /**
   * A control that is a group itself (RadioGroup, SegmentedControl) calls this from an effect: it
   * then carries the group's name, description and states, so the Field does not wrap it in a
   * second group that screen readers would announce twice. Returns the release.
   */
  adoptGroup(): () => void;
}

const KEY = Symbol('field');

export function setField(context: FieldContext): void {
  setContext(KEY, context);
}

/** The enclosing Field, if there is one. Call during component initialisation. */
export function getField(): FieldContext | undefined {
  return getContext<FieldContext | undefined>(KEY);
}

/** Space-separated id list for aria-describedby or aria-labelledby; undefined when empty. */
export function idList(...ids: (string | null | undefined | false)[]): string | undefined {
  return ids.filter(Boolean).join(' ') || undefined;
}

/**
 * A press on a field box's padding or icons puts the caret in its input, as a native field would.
 * Pointer only: keyboard users reach the input itself, so the box needs no role or key handler.
 */
export function pressFocuses(input: () => HTMLElement | null | undefined): Attachment<HTMLElement> {
  return (box) => {
    const onPress = (event: PointerEvent) => {
      if (event.target instanceof Element && event.target.closest('input, textarea, button'))
        return;
      event.preventDefault();
      input()?.focus();
    };
    box.addEventListener('pointerdown', onPress);
    return () => box.removeEventListener('pointerdown', onPress);
  };
}
