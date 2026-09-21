'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useMarkets } from '@/hooks/useMarkets';
import { Card } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { StatusBadge } from '@/components/ui/Badge';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import Pagination from '@/components/ui/Pagination';
import Button from '@/components/ui/Button';
import CreateMarketModal from './CreateMarketModal';

export default function MarketsListView({ category, title }: { category?: string; title: string }) {
  const [offset, setOffset] = useState(0);
  const [createOpen, setCreateOpen] = useState(false);
  const limit = 20;
  const { data, isLoading, isError, error } = useMarkets({ category, limit, offset });

  return (
    <Card>
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          + New market
        </Button>
      </div>

      {isLoading && <LoadingState />}
      {isError && <ErrorState message={(error as Error).message} />}

      {data && data.items.length === 0 && <EmptyState title="No markets yet" hint="Create one to get started." />}

      {data && data.items.length > 0 && (
        <Table>
          <THead>
            <Tr>
              <Th>Name</Th>
              <Th>Category</Th>
              <Th>Status</Th>
              <Th>Opening</Th>
              <Th>Closing</Th>
              <Th>Result</Th>
              <Th></Th>
            </Tr>
          </THead>
          <TBody>
            {data.items.map((market) => (
              <Tr key={market.id}>
                <Td className="font-medium text-slate-900">{market.name}</Td>
                <Td>{market.category}</Td>
                <Td>
                  <StatusBadge status={market.status} />
                </Td>
                <Td>{market.opening_time ?? '—'}</Td>
                <Td>{market.closing_time ?? '—'}</Td>
                <Td>{market.result_time ?? '—'}</Td>
                <Td>
                  <Link href={`/dashboard/markets/${market.id}`} className="text-xs font-semibold text-brand-600 hover:underline">
                    Manage →
                  </Link>
                </Td>
              </Tr>
            ))}
          </TBody>
        </Table>
      )}

      {data && <Pagination total={data.total} limit={limit} offset={offset} onOffsetChange={setOffset} />}

      <CreateMarketModal open={createOpen} onClose={() => setCreateOpen(false)} defaultCategorySlug={category} />
    </Card>
  );
}
