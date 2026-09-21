'use client';

import { useMemo } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import { useSimulations } from '@/hooks/useSimulations';
import { useMarketsLookup } from '@/hooks/useMarketsLookup';
import { useStudentsLookup } from '@/hooks/useStudents';

export default function BulkBatchesPage() {
  const { data, isLoading, isError, error } = useSimulations({ limit: 200 });
  const { byId } = useMarketsLookup();
  const { byId: studentsById } = useStudentsLookup();

  const batches = useMemo(() => {
    if (!data) return [];
    const map = new Map<number, { batchId: number; userId: number; marketId: number; gameType: string; count: number; total: number; won: number; pending: number }>();
    for (const entry of data.items) {
      const existing = map.get(entry.batchId);
      if (existing) {
        existing.count += 1;
        existing.total += entry.simulatedCredits;
        if (entry.status === 'Won') existing.won += 1;
        if (entry.status === 'Pending') existing.pending += 1;
      } else {
        map.set(entry.batchId, {
          batchId: entry.batchId,
          userId: entry.userId,
          marketId: entry.marketId,
          gameType: entry.gameType,
          count: 1,
          total: entry.simulatedCredits,
          won: entry.status === 'Won' ? 1 : 0,
          pending: entry.status === 'Pending' ? 1 : 0,
        });
      }
    }
    return Array.from(map.values())
      .filter((b) => b.count > 1)
      .sort((a, b) => b.batchId - a.batchId);
  }, [data]);

  return (
    <div>
      <PageHeader icon="play" title="Bulk Batches" description="Batches with more than one selection submitted together." />
      <Card>
        {isLoading && <LoadingState />}
        {isError && <ErrorState message={(error as Error).message} />}
        {!isLoading && batches.length === 0 && <EmptyState title="No bulk batches yet" hint="Submit 2+ selections in one batch to see it here." />}

        {batches.length > 0 && (
          <Table>
            <THead>
              <Tr>
                <Th>Batch</Th>
                <Th>User</Th>
                <Th>Market</Th>
                <Th>Game Type</Th>
                <Th>Selections</Th>
                <Th>Total Credits</Th>
                <Th>Won</Th>
                <Th>Pending</Th>
              </Tr>
            </THead>
            <TBody>
              {batches.map((b) => (
                <Tr key={b.batchId}>
                  <Td className="font-medium text-slate-900">#{b.batchId}</Td>
                  <Td>{studentsById.get(b.userId)?.name ?? `#${b.userId}`}</Td>
                  <Td>{byId.get(b.marketId)?.name ?? `#${b.marketId}`}</Td>
                  <Td>{b.gameType}</Td>
                  <Td>{b.count}</Td>
                  <Td>{b.total}</Td>
                  <Td>{b.won}</Td>
                  <Td>{b.pending}</Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
