import type { ReactElement, ReactNode } from 'react';

import { Wordmark } from './Wordmark';

interface Props {
  title: ReactNode;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}

export function AuthFrame({ title, subtitle, children, footer }: Readonly<Props>): ReactElement {
  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-6 px-4 py-10">
      <header className="flex flex-col gap-3">
        <Wordmark />
        <h1 className="text-3xl">{title}</h1>
        <p className="text-sm text-muted">{subtitle}</p>
      </header>
      <section className="rounded-2xl border border-slate bg-white p-6 shadow-sm">
        {children}
      </section>
      <p className="mx-auto w-fit rounded-full bg-white/85 px-4 py-1.5 text-center text-sm text-ink-soft backdrop-blur-sm">
        {footer}
      </p>
    </main>
  );
}

export const AUTH_LINK = 'font-semibold text-navy underline-offset-4 hover:underline';
