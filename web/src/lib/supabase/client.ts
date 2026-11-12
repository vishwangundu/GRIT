import { createBrowserClient } from '@supabase/ssr';
import type { SupabaseClient } from '@supabase/supabase-js';

import { PUBLIC_ENV, requireEnv } from '@/lib/env';

let browserClient: SupabaseClient | null = null;

/** Browser Supabase client (anon key only). Used for login and to read the access token. */
export function getSupabase(): SupabaseClient {
  browserClient ??= createBrowserClient(
    requireEnv(PUBLIC_ENV.supabaseUrl, 'NEXT_PUBLIC_SUPABASE_URL'),
    requireEnv(PUBLIC_ENV.supabaseAnonKey, 'NEXT_PUBLIC_SUPABASE_ANON_KEY'),
  );
  return browserClient;
}

export async function getAccessToken(): Promise<string | null> {
  const { data } = await getSupabase().auth.getSession();
  return data.session?.access_token ?? null;
}
