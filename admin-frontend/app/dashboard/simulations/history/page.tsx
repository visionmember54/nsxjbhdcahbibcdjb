'use client';

import { Suspense, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { FormField, Select } from '@/components/ui/Field';
import { LoadingState } from '@/components/ui/States';
import Pagination from '@/components/ui/Pagination';
import SimulationsTable from '@/components/simulations/SimulationsTable';
import { useSimulations } from '@/hooks/useSimulations';
import { useStudents } from '@/hooks/useStudents';
import { useGameTypes } from '@/hooks/useGameTypes';

const STATUSES = ['Pending', 'Won', 'Lost', 'Cancelled'];

export default function StudentHistoryPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <StudentHistoryPageInner />
    </Suspense>
  );
}

function StudentHistoryPageInner() {
  const searchParams = useSearchParams();
  const { data: studentsPage } = useStudents({ limit: 100 });
  const { data: gameTypes } = useGameTypes();
  const [studentId, setStudentId] = useState<number | ''>('');
  const [gameType, setGameType] = useState(searchParams.get('gameType') ?? '');
  const [status, setStatus] = useState(searchParams.get('status') ?? '');
  const [offset, setOffset] = useState(0);
  const limit = 20;

  const { data, isLoading, isError, error } = useSimulations({
    studentId: studentId || undefined,
    gameType: gameType || undefined,
    status: status || undefined,
    limit,
    offset,
  });

  return (
    <div>
      <PageHeader icon="play" title="User History" description="Every selection a specific user has submitted." />
      <Card>
        <div className="grid gap-4 border-b border-slate-100 p-4 sm:grid-cols-3">
          <FormField label="User">
            <Select
              value={studentId}
              onChange={(e) => {
                setStudentId(e.target.value ? Number(e.target.value) : '');
                setOffset(0);
              }}
            >
              <option value="">All users</option>
              {studentsPage?.items.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="Game type">
            <Select
              value={gameType}
              onChange={(e) => {
                setGameType(e.target.value);
                setOffset(0);
              }}
            >
              <option value="">All game types</option>
              {gameTypes?.map((gt) => (
                <option key={gt.code} value={gt.code}>
                  {gt.name}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="Status">
            <Select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setOffset(0);
              }}
            >
              <option value="">All statuses</option>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </FormField>
        </div>
        <SimulationsTable
          entries={data?.items}
          isLoading={isLoading}
          isError={isError}
          errorMessage={(error as Error)?.message}
          showStudent={!studentId}
        />
        {data && <Pagination total={data.total} limit={limit} offset={offset} onOffsetChange={setOffset} />}
      </Card>
    </div>
  );
}
