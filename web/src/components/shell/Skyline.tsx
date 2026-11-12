import type { ReactElement } from 'react';

/** Decorative skyline of world landmarks (public/skyline.png, supplied artwork with its
 * background made transparent). Fixed to the bottom of the window so it never adds scroll;
 * content renders above it. Full width on large screens; on phones it keeps a minimum
 * height and crops the sides. */
export function Skyline(): ReactElement {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-x-0 bottom-0 z-0 aspect-[2048/297] max-h-72 min-h-24 w-full bg-[url(/skyline.png)] bg-cover bg-bottom bg-no-repeat"
    />
  );
}
