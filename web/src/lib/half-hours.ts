/** "HH:MM" options on 30-minute boundaries for the availability form. */
const MINUTES_PER_HOUR = 60;
const HOURS_PER_DAY = 24;
const MINUTES_PER_DAY = HOURS_PER_DAY * MINUTES_PER_HOUR;

export function halfHourOptions(stepMinutes: number): string[] {
  const options: string[] = [];
  for (let minutes = 0; minutes < MINUTES_PER_DAY; minutes += stepMinutes) {
    const hh = String(Math.floor(minutes / MINUTES_PER_HOUR)).padStart(2, '0');
    const mm = String(minutes % MINUTES_PER_HOUR).padStart(2, '0');
    options.push(`${hh}:${mm}`);
  }
  return options;
}
