'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { type ReactElement, useState } from 'react';
import { z } from 'zod';

import { ErrorBox, Loading } from '@/components/ui/StateView';
import { useApi } from '@/hooks/use-api';
import { PATHS } from '@/lib/endpoints/paths';
import { istDateKey } from '@/lib/time';
import type { Schedule } from '@/types/models';

import { DayNav } from './DayNav';
import { DetailPanel } from './DetailPanel';
import { NoSelection } from './NoSelection';
import { ResultsBanner } from './ResultsBanner';
import { ScheduleList } from './ScheduleList';

const dateParam = z.iso.date();
const REFRESH_MS = 60_000;

export function InterviewerSchedule(): ReactElement {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const parsed = dateParam.safeParse(params.get('date'));
  const date = parsed.success ? parsed.data : istDateKey();
  const { data, error, mutate } = useApi<Schedule>(PATHS.schedule(date), REFRESH_MS);
  const [selected, setSelected] = useState<string | null>(null);

  function goTo(next: string): void {
    setSelected(null);
    router.replace(`${pathname}?date=${next}`);
  }

  return (
    <div className="flex flex-col gap-4">
      <DayNav date={date} onChange={goTo} />
      {error ? <ErrorBox error={error} onRetry={() => void mutate()} /> : null}
      {!data && !error ? <Loading label="Loading schedule…" /> : null}
      {data ? (
        <>
          <ResultsBanner items={data.to_record} selected={selected} onOpen={setSelected} />
          <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_28rem]">
            <ScheduleList
              items={data.items}
              isToday={date === istDateKey()}
              selected={selected}
              onOpen={setSelected}
            />
            <div className="lg:sticky lg:top-24">
              {selected ? (
                <DetailPanel key={selected} bookingId={selected} onChanged={() => mutate()} />
              ) : (
                <NoSelection />
              )}
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
