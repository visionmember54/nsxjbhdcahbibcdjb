'use client';

import Link from 'next/link';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import { useMarkets } from '@/hooks/useMarkets';

export default function SchedulePage() {
  const { data, isLoading, isError, error } = useMarkets({ limit: 200 });
  return <div><PageHeader icon="calendar" title="Market Schedule & Cutoffs" description="Opening, closing, result, and cutoff times. Open a market to edit its schedule or Starline slots." />
    <Card>{isLoading && <LoadingState />}{isError && <ErrorState message={(error as Error).message} />}{data?.items.length === 0 && <EmptyState title="No markets configured" />}{data && data.items.length > 0 && <Table><THead><Tr><Th>Market</Th><Th>Opening</Th><Th>Cutoff</Th><Th>Closing</Th><Th>Result</Th><Th>Timezone</Th></Tr></THead><TBody>{data.items.map((market) => <Tr key={market.id}><Td><Link className="font-medium text-brand-600 hover:underline" href={`/dashboard/markets/${market.id}`}>{market.name}</Link></Td><Td>{market.opening_time ?? '—'}</Td><Td>{market.cutoff_time ?? '—'}</Td><Td>{market.closing_time ?? '—'}</Td><Td>{market.result_time ?? '—'}</Td><Td>{market.timezone}</Td></Tr>)}</TBody></Table>}</Card>
  </div>;
}
