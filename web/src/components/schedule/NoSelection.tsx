import type { ReactElement } from 'react';

/** Detail column placeholder until an interview is picked from the list. */
export function NoSelection(): ReactElement {
  return (
    <section className="hidden rounded-2xl border border-dashed border-line-strong bg-white/60 p-6 text-center lg:block">
      <p className="text-base font-semibold">No interview selected</p>
      <p className="mt-1 text-sm text-muted">
        Pick an interview from the list to see the student, join the call and record the result.
      </p>
    </section>
  );
}
