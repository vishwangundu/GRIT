import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

import { PUBLIC_ENV } from '@/lib/env';

/** Refreshes the Supabase session cookie and reports whether a user is signed in. */
export async function updateSession(
  request: NextRequest,
): Promise<{ response: NextResponse; isSignedIn: boolean }> {
  let response = NextResponse.next({ request });
  if (!PUBLIC_ENV.supabaseUrl || !PUBLIC_ENV.supabaseAnonKey) {
    return { response, isSignedIn: false };
  }
  const supabase = createServerClient(PUBLIC_ENV.supabaseUrl, PUBLIC_ENV.supabaseAnonKey, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll: (cookiesToSet) => {
        for (const { name, value } of cookiesToSet) request.cookies.set(name, value);
        response = NextResponse.next({ request });
        for (const { name, value, options } of cookiesToSet) {
          response.cookies.set(name, value, options);
        }
      },
    },
  });
  const { data } = await supabase.auth.getUser();
  return { response, isSignedIn: data.user !== null };
}
