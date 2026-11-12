import { describe, expect, it } from 'vitest';

import { safeNextPath } from './roles';

describe('safeNextPath', () => {
  it('keeps a path inside the role area', () => {
    expect(safeNextPath('/student/book', 'student')).toBe('/student/book');
  });

  it('sends users home when the path belongs to another role', () => {
    expect(safeNextPath('/admin', 'student')).toBe('/student');
  });

  it('rejects external and malformed targets', () => {
    expect(safeNextPath('https://evil.example', 'admin')).toBe('/admin');
    expect(safeNextPath('//evil.example', 'interviewer')).toBe('/interviewer');
    expect(safeNextPath(null, 'interviewer')).toBe('/interviewer');
  });
});
