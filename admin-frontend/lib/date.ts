/** YYYY-MM-DD in the browser's local timezone (not UTC).
 * `toISOString().slice(0, 10)` is the classic trap here -- it converts to
 * UTC first, so it's off by a day for roughly 5.5 hours a day for an
 * India-based admin (UTC+5:30). `toLocaleDateString('en-CA')` gives the same
 * YYYY-MM-DD shape but reads the local calendar date instead. */
export function todayLocalIso(): string {
  return new Date().toLocaleDateString('en-CA');
}

export function daysAgoLocalIso(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toLocaleDateString('en-CA');
}
