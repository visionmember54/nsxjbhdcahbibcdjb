'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import { StatusBadge } from '@/components/ui/Badge';
import { usePermissions } from '@/hooks/usePermissions';
import { SimulationEntry } from '@/lib/api/types';
import EditBidModal from './EditBidModal';

function formatBidId(id: number): string {
  return `BID${String(id).padStart(6, '0')}`;
}

export default function BidHistoryTable({
  entries,
  isLoading,
  isError,
  errorMessage,
}: {
  entries: SimulationEntry[] | undefined;
  isLoading: boolean;
  isError: boolean;
  errorMessage?: string;
}) {
  const { has } = usePermissions();
  const canEdit = has('simulations.create');
  const [editing, setEditing] = useState<SimulationEntry | null>(null);

  return (
    <div>
      {isLoading && <LoadingState />}
      {isError && <ErrorState message={errorMessage ?? 'Failed to load'} />}
      {entries && entries.length === 0 && <EmptyState title="No bids yet" />}

      {entries && entries.length > 0 && (
        <div className="overflow-x-auto">
          <Table>
            <THead>
              <Tr>
                <Th>User Name</Th>
                <Th>Bid TX ID</Th>
                <Th>Game Name</Th>
                <Th>Game Type</Th>
                <Th>Session</Th>
                <Th>Open Paana</Th>
                <Th>Open Digit</Th>
                <Th>Close Paana</Th>
                <Th>Close Digit</Th>
                <Th>Points</Th>
                <Th>Status</Th>
                <Th></Th>
              </Tr>
            </THead>
            <TBody>
              {entries.map((e) => (
                <Tr key={e.id}>
                  <Td className="font-medium text-slate-900">
                    <Link href={`/dashboard/students/${e.userId}`} className="text-brand-700 hover:underline">
                      {e.userName ?? `#${e.userId}`}
                    </Link>
                  </Td>
                  <Td className="font-mono text-xs">{formatBidId(e.id)}</Td>
                  <Td>{e.marketName ?? `#${e.marketId}`}</Td>
                  <Td>{e.gameType}</Td>
                  <Td>{e.stage ?? '—'}</Td>
                  <Td>{e.openPaana ?? 'N/A'}</Td>
                  <Td>{e.openDigit ?? 'N/A'}</Td>
                  <Td>{e.closePaana ?? 'N/A'}</Td>
                  <Td>{e.closeDigit ?? 'N/A'}</Td>
                  <Td>{e.simulatedCredits}</Td>
                  <Td>
                    <StatusBadge status={e.status} />
                  </Td>
                  <Td>
                    {canEdit && e.status === 'Pending' ? (
                      <button className="text-xs font-semibold text-brand-600 hover:underline" onClick={() => setEditing(e)}>
                        Edit
                      </button>
                    ) : (
                      <span className="text-xs text-slate-300">—</span>
                    )}
                  </Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        </div>
      )}

      <EditBidModal entry={editing} onClose={() => setEditing(null)} />
    </div>
  );
}
