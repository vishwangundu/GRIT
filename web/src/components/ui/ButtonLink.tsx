import Link from 'next/link';
import type { ReactElement, ReactNode } from 'react';

import { BUTTON_BASE, BUTTON_VARIANTS } from './Button';

interface Props {
  href: string;
  children: ReactNode;
  variant?: 'primary' | 'secondary';
  isExternal?: boolean;
}

export function ButtonLink({
  href,
  children,
  variant = 'primary',
  isExternal = false,
}: Readonly<Props>): ReactElement {
  const className = `${BUTTON_BASE} ${BUTTON_VARIANTS[variant]}`;
  if (isExternal) {
    return (
      <a href={href} target="_blank" rel="noreferrer" className={className}>
        {children} <span aria-hidden="true">→</span>
      </a>
    );
  }
  return (
    <Link href={href} className={className}>
      {children} <span aria-hidden="true">→</span>
    </Link>
  );
}
