'use client';

import { Suspense, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { FormField, Select, Input } from '@/components/ui/Field';
import Button from '@/components/ui/Button';
import { LoadingState } from '@/components/ui/States';
import Pagination from '@/components/ui/Pagination';
import BidHistoryTable from '@/components/simulations/BidHistoryTable';
import { useSimulations } from '@/hooks/useSimulations';
import { useStudents } from '@/hooks/useStudents';
import { useGameTypes } from '@/hooks/useGameTypes';
import { useMarkets } from '@/hooks/useMarkets';

const STATUSES = ['Pending', 'Won', 'Lost', 'Cancelled'];

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

interface Filters {
  date: string;
  marketId: number | '';
  gameType: string;
  status: string;
  studentId: number | '';
}

export default function BidHistoryPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <BidHistoryPageInner />
    </Suspense>
  );
}

function BidHistoryPageInner() {
  const searchParams = useSearchParams();
  const { data: marketsPage } = useMarkets({ limit: 200 });
  const { data: studentsPage } = useStudents({ limit: 200 });
  const { data: gameTypes } = useGameTypes();

  const initial: Filters = {
    date: '',
    marketId: '',
    gameType: searchParams.get('gameType') ?? '',
    status: searchParams.get('status') ?? '',
    studentId: '',
  };

  const [draft, setDraft] = useState<Filters>(initial);
  const [applied, setApplied] = useState<Filters>(initial);
  const [offset, setOffset] = useState(0);
  const limit = 20;

  const { data, isLoading, isError, error } = useSimulations({
    studentId: applied.studentId || undefined,
    marketId: applied.marketId || undefined,
    gameType: applied.gameType || undefined,
    status: applied.status || undefined,
    date: applied.date || undefined,
    limit,
    offset,
  });

  return (
    <div>
      <PageHeader icon="play" title="Bid History" description="Every selection placed, filterable by date, market, game type, and status." />
      <Card>
        <div className="grid gap-4 border-b border-slate-100 p-4 sm:grid-cols-2 lg:grid-cols-5">
          <FormField label="Date">
            <Input type="date" value={draft.date} onChange={(e) => setDraft({ ...draft, date: e.target.value })} />
          </FormField>
          <FormField label="Game Name">
            <Select value={draft.marketId} onChange={(e) => setDraft({ ...draft, marketId: e.target.value ? Number(e.target.value) : '' })}>
              <option value="">All markets</option>
              {marketsPage?.items.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="Game Type">
            <Select value={draft.gameType} onChange={(e) => setDraft({ ...draft, gameType: e.target.value })}>
              <option value="">All types</option>
              {gameTypes?.map((gt) => (
                <option key={gt.code} value={gt.code}>
                  {gt.name}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="Status">
            <Select value={draft.status} onChange={(e) => setDraft({ ...draft, status: e.target.value })}>
              <option value="">All statuses</option>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="User">
            <Select value={draft.studentId} onChange={(e) => setDraft({ ...draft, studentId: e.target.value ? Number(e.target.value) : '' })}>
              <option value="">All users</option>
              {studentsPage?.items.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </Select>
          </FormField>
        </div>
        <div className="flex justify-end gap-2 border-b border-slate-100 px-4 py-3">
          <Button
            variant="secondary"
            onClick={() => {
              const cleared: Filters = { date: '', marketId: '', gameType: '', status: '', studentId: '' };
              setDraft(cleared);
              setApplied(cleared);
              setOffset(0);
            }}
          >
            Clear
          </Button>
          <Button
            onClick={() => {
              setApplied(draft);
              setOffset(0);
            }}
          >
            Submit
          </Button>
        </div>
        <BidHistoryTable
          entries={data?.items}
          isLoading={isLoading}
          isError={isError}
          errorMessage={(error as Error)?.message}
        />
        {data && <Pagination total={data.total} limit={limit} offset={offset} onOffsetChange={setOffset} />}
      </Card>
    </div>
  );
}
