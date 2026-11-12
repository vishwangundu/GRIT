import { describe, expect, it } from 'vitest';

import { initialsOf } from './initials';

describe('initialsOf', () => {
  it('uses the first and last word', () => {
    expect(initialsOf('Priya Sharma')).toBe('PS');
    expect(initialsOf('Harsha Vardhan Rao')).toBe('HR');
  });

  it('handles a single word and extra spaces', () => {
    expect(initialsOf('  int1 ')).toBe('I');
  });

  it('falls back when the name is missing', () => {
    expect(initialsOf(undefined)).toBe('?');
    expect(initialsOf('   ')).toBe('?');
  });
});
