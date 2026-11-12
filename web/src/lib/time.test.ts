import { describe, expect, it } from 'vitest';

import {
  addDays,
  dayLabel,
  formatDate,
  formatDuration,
  formatRange,
  formatTime,
  istDateKey,
} from './time';

describe('IST formatting', () => {
  it('formats a UTC instant as an IST date like the notifications', () => {
    expect(formatDate('2026-11-19T11:00:00Z')).toBe('Thu, 19 Nov');
  });

  it('formats times in 12-hour IST', () => {
    expect(formatTime('2026-11-19T11:00:00Z')).toBe('4:30 PM');
    expect(formatTime('2026-11-19T18:30:00Z')).toBe('12:00 AM');
    expect(formatTime('2026-11-19T06:30:00Z')).toBe('12:00 PM');
  });

  it('formats a slot range with the IST suffix', () => {
    expect(formatRange('2026-11-19T11:00:00Z', '2026-11-19T11:30:00Z')).toBe(
      '4:30 PM – 5:00 PM IST',
    );
  });

  it('uses the IST calendar day, not the UTC one', () => {
    expect(istDateKey(new Date('2026-11-19T20:00:00Z'))).toBe('2026-11-20');
    expect(istDateKey(new Date('2026-11-19T18:00:00Z'))).toBe('2026-11-19');
  });

  it('shifts date keys across month ends', () => {
    expect(addDays('2026-11-30', 1)).toBe('2026-12-01');
    expect(addDays('2026-11-01', -1)).toBe('2026-10-31');
  });

  it('labels a day for the day strip', () => {
    expect(dayLabel('2026-11-19')).toEqual({ weekday: 'Thu', day: '19', month: 'Nov' });
  });

  it('formats durations', () => {
    expect(formatDuration(45 * 60_000)).toBe('45 min');
    expect(formatDuration(135 * 60_000)).toBe('2 h 15 min');
    expect(formatDuration(3 * 86_400_000)).toBe('3 d');
    expect(formatDuration(-5)).toBe('0 min');
  });
});
