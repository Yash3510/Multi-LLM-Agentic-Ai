// Following a streaming answer: the thread keeps to its newest text only while the reader is at
// the end of it; scrolling up to read stops that until they come back down.

/** Within `slack` px of the end of the scroll area. */
export function nearBottom(
  {
    scrollTop,
    scrollHeight,
    clientHeight,
  }: Pick<HTMLElement, 'scrollTop' | 'scrollHeight' | 'clientHeight'>,
  slack = 80,
): boolean {
  return scrollHeight - scrollTop - clientHeight <= slack;
}
