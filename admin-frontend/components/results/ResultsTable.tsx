'use client';

import { useConfirm } from '@/components/ui/Feedback';
import { useState } from 'react';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import { StatusBadge } from '@/components/ui/Badge';
import { useMarketsLookup } from '@/hooks/useMarketsLookup';
import { usePermissions } from '@/hooks/usePermissions';
import { usePublishDraft, useDeleteResult } from '@/hooks/useResults';
import { MarketResult } from '@/lib/api/types';
import CorrectResultModal from './CorrectResultModal';

export default function ResultsTable({
  results,
  isLoading,
  isError,
  errorMessage,
}: {
  results: MarketResult[] | undefined;
  isLoading: boolean;
  isError: boolean;
  errorMessage?: string;
}) {
  const { byId } = useMarketsLookup();
  const { has } = usePermissions();
  const publishDraft = usePublishDraft();
  const confirm = useConfirm();
  const deleteResult = useDeleteResult();
  const [correcting, setCorrecting] = useState<MarketResult | null>(null);

  return (
    <div>
      {isLoading && <LoadingState />}
      {isError && <ErrorState message={errorMessage ?? 'Failed to load'} />}
      {results && results.length === 0 && <EmptyState title="No results here" />}

      {results && results.length > 0 && (
        <Table>
          <THead>
            <Tr>
              <Th>Market</Th>
              <Th>Date</Th>
              <Th>Open</Th>
              <Th>Close</Th>
              <Th>Jodi</Th>
              <Th>Status</Th>
              <Th></Th>
            </Tr>
          </THead>
          <TBody>
            {results.map((r) => (
              <Tr key={r.id}>
                <Td className="font-medium text-slate-900">{byId.get(r.marketId)?.name ?? `#${r.marketId}`}</Td>
                <Td>{r.date}</Td>
                <Td>{r.openPanna ? `${r.openPanna} (${r.openAnk})` : r.openAnk ?? r.singleResult ?? '—'}</Td>
                <Td>{r.closePanna ? `${r.closePanna} (${r.closeAnk})` : r.closeAnk ?? '—'}</Td>
                <Td>{r.jodi ?? '—'}</Td>
                <Td>
                  <StatusBadge status={r.status} />
                </Td>
                <Td className="space-x-3">
                  {r.status === 'Draft' && has('results.manage') && (
                    <button
                      className="text-xs font-semibold text-brand-600 hover:underline"
                      onClick={() => publishDraft.mutate(r.id)}
                    >
                      Publish
                    </button>
                  )}
                  {r.status === 'Published' && has('results.correct') && (
                    <button className="text-xs font-semibold text-amber-600 hover:underline" onClick={() => setCorrecting(r)}>
                      Correct
                    </button>
                  )}
                  {has('results.delete') && (
                    <button
                      className="text-xs font-semibold text-red-600 hover:underline"
                      onClick={async () => {
                        if (await confirm('Delete this result record?')) deleteResult.mutate(r.id);
                      }}
                    >
                      Delete
                    </button>
                  )}
                </Td>
              </Tr>
            ))}
          </TBody>
        </Table>
      )}

      <CorrectResultModal result={correcting} onClose={() => setCorrecting(null)} />
    </div>
  );
}
