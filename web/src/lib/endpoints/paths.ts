/** API paths, also used as SWR cache keys. */
export const PATHS = {
  me: '/me',
  rules: '/rules',
  registrationOptions: '/registration-options',
  dashboard: '/student/dashboard',
  slots: '/student/slots',
  notifications: '/student/notifications',
  leaderboard: (tier: 'qual' | 'pre') => `/student/leaderboard?tier=${tier}`,
  schedule: (date: string) => `/interviewer/schedule?date=${date}`,
  interview: (bookingId: string) => `/interviewer/interviews/${bookingId}`,
  availability: '/interviewer/availability',
  tracker: (tab: string, badgeId: number | null) => {
    const query = new URLSearchParams({ tab });
    if (badgeId !== null) query.set('badge_id', String(badgeId));
    return `/admin/tracker?${query.toString()}`;
  },
  reassignOptions: (bookingId: string) => `/admin/bookings/${bookingId}/reassign-options`,
} as const;
