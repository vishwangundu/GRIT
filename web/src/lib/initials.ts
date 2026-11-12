/** Up to two initials for an avatar: first and last word of the name ("Priya Sharma" → "PS"). */
export function initialsOf(name: string | null | undefined): string {
  const words = (name ?? '').trim().split(/\s+/u).filter(Boolean);
  const first = words.at(0)?.charAt(0) ?? '';
  const last = words.length > 1 ? (words.at(-1)?.charAt(0) ?? '') : '';
  return (first + last).toUpperCase() || '?';
}
