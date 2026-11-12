import { describe, expect, it } from 'vitest';

import { halfHourOptions } from './half-hours';
import { CHIP_LABELS, plural, stateLabel } from './labels';
import { asTone } from './tones';

describe('labels', () => {
  it('pluralises counts', () => {
    expect(plural(1, 'attempt')).toBe('1 attempt');
    expect(plural(2, 'attempt')).toBe('2 attempts');
  });

  it('labels states and falls back to the raw value', () => {
    expect(stateLabel('awaiting_result')).toBe('Awaiting result');
    expect(stateLabel('mystery')).toBe('mystery');
  });

  it('gives every chip text, not just colour', () => {
    expect(Object.values(CHIP_LABELS).every((c) => c.label.length > 0)).toBe(true);
  });

  it('maps unknown tones to neutral', () => {
    expect(asTone('success')).toBe('success');
    expect(asTone('loud')).toBe('neutral');
  });

  it('lists 48 half-hour options', () => {
    const options = halfHourOptions(30);
    expect(options).toHaveLength(48);
    expect(options.slice(0, 2)).toEqual(['00:00', '00:30']);
  });
});
