import type { Metadata, Viewport } from 'next';
import { DM_Sans, Familjen_Grotesk } from 'next/font/google';
import type { ReactElement, ReactNode } from 'react';

import './globals.css';

const display = Familjen_Grotesk({ subsets: ['latin'], variable: '--font-familjen' });
const body = DM_Sans({ subsets: ['latin'], variable: '--font-dm-sans' });

export const metadata: Metadata = {
  title: 'GRIT Interviews | NIAT',
  description: 'Book, run and track GRIT Level Clearance Interviews.',
};

export const viewport: Viewport = { width: 'device-width', initialScale: 1, themeColor: '#1a1615' };

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>): ReactElement {
  return (
    <html lang="en-IN" className={`${display.variable} ${body.variable}`}>
      <body className="min-h-dvh antialiased">{children}</body>
    </html>
  );
}
