'use client';

import { useState } from 'react';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import { StatusBadge } from '@/components/ui/Badge';
import { useMarketsLookup } from '@/hooks/useMarketsLookup';
import { useStudentsLookup } from '@/hooks/useStudents';
import { usePermissions } from '@/hooks/usePermissions';
import { SimulationEntry } from '@/lib/api/types';
import OverrideOutcomeModal from './OverrideOutcomeModal';

export default function SimulationsTable({
  entries,
  isLoading,
  isError,
  errorMessage,
  showStudent = true,
}: {
  entries: SimulationEntry[] | undefined;
  isLoading: boolean;
  isError: boolean;
  errorMessage?: string;
  showStudent?: boolean;
}) {
  const { byId } = useMarketsLookup();
  const { byId: studentsById } = useStudentsLookup();
  const { has } = usePermissions();
  const canOverride = has('simulations.override');
  const [overriding, setOverriding] = useState<SimulationEntry | null>(null);

  return (
    <div>
      {isLoading && <LoadingState />}
      {isError && <ErrorState message={errorMessage ?? 'Failed to load'} />}
      {entries && entries.length === 0 && <EmptyState title="No simulations yet" />}

      {entries && entries.length > 0 && (
        <Table>
          <THead>
            <Tr>
              {showStudent && <Th>User</Th>}
              <Th>Market</Th>
              <Th>Game Type</Th>
              <Th>Stage</Th>
              <Th>Selection</Th>
              <Th>Credits</Th>
              <Th>Potential Return</Th>
              <Th>Status</Th>
              <Th>Batch</Th>
              {canOverride && <Th></Th>}
            </Tr>
          </THead>
          <TBody>
            {entries.map((e) => (
              <Tr key={e.id}>
                {showStudent && <Td className="font-medium text-slate-900">{studentsById.get(e.userId)?.name ?? `#${e.userId}`}</Td>}
                <Td className="font-medium text-slate-900">{byId.get(e.marketId)?.name ?? `#${e.marketId}`}</Td>
                <Td>{e.gameType}</Td>
                <Td>{e.stage ?? '—'}</Td>
                <Td className="font-mono">{e.selection}</Td>
                <Td>{e.simulatedCredits}</Td>
                <Td>{e.simulatedReturn}</Td>
                <Td>
                  <StatusBadge status={e.status} />
                  {e.overrideStatus === 'OVERRIDDEN' && (
                    <span className="ml-1 text-[10px] font-semibold uppercase text-purple-600">overridden</span>
                  )}
                </Td>
                <Td>#{e.batchId}</Td>
                {canOverride && (
                  <Td>
                    {(e.status === 'Won' || e.status === 'Lost') && (
                      <button className="text-xs font-semibold text-purple-600 hover:underline" onClick={() => setOverriding(e)}>
                        Override
                      </button>
                    )}
                  </Td>
                )}
              </Tr>
            ))}
          </TBody>
        </Table>
      )}

      <OverrideOutcomeModal entry={overriding} onClose={() => setOverriding(null)} />
    </div>
  );
}
