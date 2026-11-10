// A small built-in emoji set for reactions, with names to search by (no emoji data package).

export const EMOJI: [string, string][] = [
  ['👍', 'thumbs up yes'],
  ['👎', 'thumbs down no'],
  ['❤️', 'heart love'],
  ['😂', 'laugh joy'],
  ['😊', 'smile happy'],
  ['😮', 'wow surprised'],
  ['😢', 'sad cry'],
  ['😡', 'angry'],
  ['🎉', 'party celebrate'],
  ['🙏', 'thanks please'],
  ['👏', 'clap applause'],
  ['🔥', 'fire hot'],
  ['✅', 'check done'],
  ['❌', 'cross no'],
  ['⚠️', 'warning'],
  ['👀', 'eyes looking'],
  ['💡', 'idea bulb'],
  ['🚀', 'rocket launch'],
  ['🤔', 'thinking'],
  ['🙌', 'raised hands hooray'],
  ['💯', 'hundred perfect'],
  ['⭐', 'star'],
  ['📌', 'pin'],
  ['📎', 'paperclip attach'],
  ['⏰', 'alarm clock time'],
  ['☕', 'coffee break'],
  ['👋', 'wave hello'],
  ['🤝', 'handshake deal'],
  ['😅', 'sweat relief'],
  ['🎯', 'target goal'],
];

/** Emoji whose names match the search words. */
export const findEmoji = (query: string) => {
  const words = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
  return EMOJI.filter(([, name]) => words.every((word) => name.includes(word)));
};
