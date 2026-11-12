/**
 * The only place that converts UTC <-> IST. The API always sends ISO UTC strings.
 * IST has no DST, so a fixed +05:30 offset is exact.
 */
const TZ = 'Asia/Kolkata';
const MS_PER_MINUTE = 60_000;
const IST_OFFSET_MINUTES = 330;
const IST_OFFSET_MS = IST_OFFSET_MINUTES * MS_PER_MINUTE;
const MINUTES_PER_HOUR = 60;
const DATE_KEY_LENGTH = 10;
const MS_PER_HOUR = 3_600_000;
const MS_PER_DAY = 86_400_000;
const NOON = 12;

const dateFmt = new Intl.DateTimeFormat('en-IN', {
  timeZone: TZ,
  weekday: 'short',
  day: 'numeric',
  month: 'short',
});
const partsFmt = new Intl.DateTimeFormat('en-IN', {
  timeZone: TZ,
  weekday: 'short',
  day: 'numeric',
  month: 'short',
  hour: 'numeric',
  minute: '2-digit',
  hour12: true,
});

function part(date: Date, type: Intl.DateTimeFormatPartTypes): string {
  return partsFmt.formatToParts(date).find((p) => p.type === type)?.value ?? '';
}

/** "Thu, 19 Nov" */
export function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${part(d, 'weekday')}, ${part(d, 'day')} ${part(d, 'month')}`;
}

/** "4:30 PM" */
export function formatTime(iso: string): string {
  const shifted = new Date(new Date(iso).getTime() + IST_OFFSET_MS);
  const hours = shifted.getUTCHours();
  const minutes = String(shifted.getUTCMinutes()).padStart(2, '0');
  const hour12 = hours % NOON === 0 ? NOON : hours % NOON;
  return `${String(hour12)}:${minutes} ${hours < NOON ? 'AM' : 'PM'}`;
}

/** "Thu, 19 Nov · 4:30 PM" */
export function formatDateTime(iso: string): string {
  return `${formatDate(iso)} · ${formatTime(iso)}`;
}

/** "4:30 PM – 5:00 PM IST" */
export function formatRange(startIso: string, endIso: string): string {
  return `${formatTime(startIso)} – ${formatTime(endIso)} IST`;
}

/** IST calendar date "YYYY-MM-DD" for an instant (defaults to now). */
export function istDateKey(at: Date = new Date()): string {
  return new Date(at.getTime() + IST_OFFSET_MS).toISOString().slice(0, DATE_KEY_LENGTH);
}

/** Shift a "YYYY-MM-DD" key by whole days. */
export function addDays(dateKey: string, days: number): string {
  const base = Date.parse(`${dateKey}T00:00:00Z`);
  return new Date(base + days * MS_PER_DAY).toISOString().slice(0, DATE_KEY_LENGTH);
}

/** Day strip label for a "YYYY-MM-DD" key: { weekday: "Thu", day: "19", month: "Nov" } */
export function dayLabel(dateKey: string): { weekday: string; day: string; month: string } {
  const noonIst = new Date(`${dateKey}T06:30:00Z`);
  const [weekday = '', rest = ''] = dateFmt.format(noonIst).split(', ');
  const [day = '', month = ''] = rest.split(' ');
  return { weekday, day, month };
}

/** Whole IST hours and minutes of an instant, for placing the "now" line. */
export function istMinutesOfDay(iso: string): number {
  const shifted = new Date(new Date(iso).getTime() + IST_OFFSET_MS);
  return shifted.getUTCHours() * MINUTES_PER_HOUR + shifted.getUTCMinutes();
}

/** "2 h 15 min", "45 min", "3 d" for a positive duration in ms. */
export function formatDuration(ms: number): string {
  const safe = Math.max(ms, 0);
  if (safe >= MS_PER_DAY) return `${String(Math.floor(safe / MS_PER_DAY))} d`;
  const hours = Math.floor(safe / MS_PER_HOUR);
  const minutes = Math.floor((safe % MS_PER_HOUR) / MS_PER_MINUTE);
  return hours > 0 ? `${String(hours)} h ${String(minutes)} min` : `${String(minutes)} min`;
}

export function msUntil(iso: string, now: Date = new Date()): number {
  return new Date(iso).getTime() - now.getTime();
}
