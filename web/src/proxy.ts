import { NextResponse, type NextRequest } from 'next/server';

import { updateSession } from '@/lib/supabase/proxy';

const PROTECTED = ['/student', '/interviewer', '/admin'];

/** Optimistic auth check only. FastAPI enforces every permission. */
export async function proxy(request: NextRequest): Promise<NextResponse> {
  const { response, isSignedIn } = await updateSession(request);
  const path = request.nextUrl.pathname;
  const isProtected = PROTECTED.some((prefix) => path.startsWith(prefix));
  if (isProtected && !isSignedIn) {
    const login = new URL('/login', request.url);
    login.searchParams.set('next', path);
    return NextResponse.redirect(login);
  }
  return response;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
