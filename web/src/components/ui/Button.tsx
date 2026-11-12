import type { ButtonHTMLAttributes, ReactElement, ReactNode } from 'react';

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost' | 'navy';

/** App buttons: GRIT blue primary, light outlined secondary. */
export const BUTTON_VARIANTS: Record<Variant, string> = {
  primary:
    'bg-grit-blue-strong text-white border border-grit-blue-strong hover:bg-[#244fbf] disabled:bg-[#a9bdf0] disabled:border-[#a9bdf0]',
  secondary: 'bg-white text-ink border border-line-strong hover:bg-sand disabled:text-muted',
  danger:
    'bg-grit-red-strong text-white border border-grit-red-strong hover:bg-[#9e2c31] disabled:opacity-50',
  ghost: 'text-grit-blue-strong hover:bg-select disabled:text-muted disabled:hover:bg-transparent',
  navy: 'bg-navy text-white border border-navy hover:bg-navy-strong disabled:opacity-60',
};

export const BUTTON_BASE =
  'inline-flex min-h-10 items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed';

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  isBusy?: boolean;
}

export function Button({
  variant = 'primary',
  isBusy = false,
  className = '',
  disabled,
  children,
  type = 'button',
  ...rest
}: Readonly<Props>): ReactElement {
  return (
    <button
      type={type}
      disabled={disabled === true || isBusy}
      aria-busy={isBusy}
      className={`${BUTTON_BASE} ${BUTTON_VARIANTS[variant]} relative ${className}`}
      {...rest}
    >
      {isBusy ? <BusyContent>{children}</BusyContent> : children}
    </button>
  );
}

/** Spinner over the hidden label, so the button keeps its width while busy. */
function BusyContent({ children }: Readonly<{ children: ReactNode }>): ReactElement {
  return (
    <>
      <span className="invisible inline-flex items-center gap-2">{children}</span>
      <span className="absolute inset-0 flex items-center justify-center">
        <span
          aria-hidden="true"
          className="h-5 w-5 animate-spin rounded-full border-2 border-current border-t-transparent"
        />
        <span className="sr-only">Working…</span>
      </span>
    </>
  );
}
