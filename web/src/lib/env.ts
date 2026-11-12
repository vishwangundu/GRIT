/** Public env vars. Missing values surface as a clear error at first use, not at build. */
export const PUBLIC_ENV = {
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL ?? '',
  supabaseAnonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? '',
  apiUrl: process.env.NEXT_PUBLIC_API_URL ?? '',
} as const;

export function requireEnv(value: string, name: string): string {
  if (!value) throw new Error(`${name} is not set`);
  return value;
}
