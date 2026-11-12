import { type ReactElement, Suspense } from 'react';

import { InterviewerSchedule } from '@/components/schedule/InterviewerSchedule';
import { Loading } from '@/components/ui/StateView';

export default function InterviewerPage(): ReactElement {
  return (
    <Suspense fallback={<Loading />}>
      <InterviewerSchedule />
    </Suspense>
  );
}
