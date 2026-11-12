'use client';

import { type InputHTMLAttributes, type ReactElement, useState } from 'react';

import { INPUT_CLASS } from './Field';

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'>;

function EyeIcon({ isOpen }: Readonly<{ isOpen: boolean }>): ReactElement {
  return (
    <svg
      viewBox="0 0 24 24"
      className="size-5"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      aria-hidden="true"
    >
      <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" strokeLinejoin="round" />
      <circle cx="12" cy="12" r="3" />
      {isOpen ? null : <path d="M4 4l16 16" strokeLinecap="round" />}
    </svg>
  );
}

/** Password field with a show/hide toggle. */
export function PasswordInput({ className = '', ...rest }: Readonly<Props>): ReactElement {
  const [isVisible, setIsVisible] = useState(false);
  return (
    <div className="relative">
      <input
        {...rest}
        type={isVisible ? 'text' : 'password'}
        className={`${INPUT_CLASS} w-full pr-11 ${className}`}
      />
      <button
        type="button"
        onClick={() => {
          setIsVisible((v) => !v);
        }}
        aria-label={isVisible ? 'Hide password' : 'Show password'}
        aria-pressed={isVisible}
        className="absolute inset-y-0 right-0 flex w-11 items-center justify-center rounded-r-lg text-muted hover:text-navy"
      >
        <EyeIcon isOpen={!isVisible} />
      </button>
    </div>
  );
}
