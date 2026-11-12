'use client';

import { type ReactElement, useState } from 'react';

import { ChipTabs } from '@/components/ui/ChipTabs';
import { INPUT_CLASS } from '@/components/ui/Field';
import { ErrorBox, Loading } from '@/components/ui/StateView';
import { useApi } from '@/hooks/use-api';
import { PATHS } from '@/lib/endpoints/paths';
import { filterUsers, type RoleFilter } from '@/lib/users';
import type { UsersResponse } from '@/types/models';

import { UsersTable } from './UsersTable';

function RoleTabs({
  data,
  value,
  onChange,
}: Readonly<{
  data: UsersResponse;
  value: RoleFilter;
  onChange: (role: RoleFilter) => void;
}>): ReactElement {
  const { counts } = data;
  return (
    <ChipTabs
      label="Filter by role"
      value={value}
      onChange={onChange}
      options={[
        { key: 'all', label: 'All', count: data.users.length },
        { key: 'student', label: 'Students', count: counts.student },
        { key: 'interviewer', label: 'Interviewers', count: counts.interviewer },
        { key: 'admin', label: 'Admins', count: counts.admin },
      ]}
    />
  );
}

/** Admin Users: everyone with an account, their role and email. */
export function UsersView(): ReactElement {
  const { data, error, mutate } = useApi<UsersResponse>(PATHS.users);
  const [role, setRole] = useState<RoleFilter>('all');
  const [query, setQuery] = useState('');

  return (
    <div className="grit-fill flex flex-col gap-4">
      <h1 className="text-3xl">Users</h1>
      {error ? <ErrorBox error={error} onRetry={() => void mutate()} /> : null}
      {!error && !data ? <Loading label="Loading users…" /> : null}
      {data ? (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <RoleTabs data={data} value={role} onChange={setRole} />
            <input
              type="search"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
              }}
              placeholder="Search name or email"
              aria-label="Search users by name or email"
              className={`${INPUT_CLASS} w-full sm:w-72`}
            />
          </div>
          <UsersTable users={filterUsers(data.users, role, query)} />
        </>
      ) : null}
    </div>
  );
}
