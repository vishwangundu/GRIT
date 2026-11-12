import { type ReactElement, type ReactNode, useId } from 'react';

import { PersonName } from '@/components/ui/Avatar';
import { Empty } from '@/components/ui/StateView';

interface Props {
  headers: readonly string[];
  isEmpty: boolean;
  emptyText: string;
  children: ReactNode;
}

/** Phone layout labels: each cell shows its column header before the value (globals.css
 * turns rows into cards). The first column is the card's title, so it gets no label. */
function mobileLabels(scope: string, headers: readonly string[]): string {
  const rules = headers.map((header, index) => {
    const cell = `.${scope} td:nth-child(${String(index + 1)})`;
    if (index === 0) return '';
    if (header === '') return `${cell}{justify-content:flex-end}`;
    return `${cell}::before{content:${JSON.stringify(header)}}`;
  });
  return `@media (max-width: 767.98px){${rules.join('')}}`;
}

export function Table({ headers, isEmpty, emptyText, children }: Readonly<Props>): ReactElement {
  const scope = `grit-table-${useId().replace(/[^a-zA-Z0-9]/g, '')}`;
  if (isEmpty) return <Empty>{emptyText}</Empty>;
  return (
    <div className="grit-table-wrap grit-scroll overflow-x-auto grit-panel">
      <style>{mobileLabels(scope, headers)}</style>
      <table className={`grit-table ${scope} w-full min-w-[40rem] text-sm`}>
        <thead className="bg-ink text-left text-xs tracking-wide text-white/85 uppercase">
          <tr>
            {headers.map((h) => (
              <th key={h} scope="col" className="px-3 py-3.5 font-semibold">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export const CELL = 'border-t border-ink/10 px-3 py-2 align-middle';

export function StudentCell({
  name,
  campus,
}: Readonly<{ name: string; campus: string }>): ReactElement {
  return (
    <td className={CELL}>
      <PersonName name={name} detail={campus} />
    </td>
  );
}

/** Interviewer name with avatar, for the tracker tables. */
export function InterviewerCell({ name }: Readonly<{ name: string }>): ReactElement {
  return (
    <td className={CELL}>
      <PersonName name={name} nameClassName="" />
    </td>
  );
}
