'use client';

import { useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import Badge from '@/components/ui/Badge';
import { FormField, Select } from '@/components/ui/Field';
import Pagination from '@/components/ui/Pagination';
import { useGlobalCreditLedger } from '@/hooks/useCreditLedger';

const TYPE_TONE: Record<string, 'green' | 'blue' | 'purple' | 'amber' | 'slate'> = {
  grant: 'green',
  adjustment: 'blue',
  reset: 'purple',
  stake: 'slate',
  payout: 'amber',
};

const TYPES = ['grant', 'adjustment', 'reset', 'stake', 'payout'];

export default function AllTransactionsPage() {
  const [type, setType] = useState('');
  const [offset, setOffset] = useState(0);
  const limit = 25;
  const { data, isLoading, isError, error } = useGlobalCreditLedger({ limit, offset, type: type || undefined });

  return (
    <div>
      <PageHeader
        icon="chart"
        title="All Transactions"
        description="Every credit ledger entry, across every user — grants, adjustments, resets, stakes, and payouts."
      />
      <Card>
        <div className="border-b border-slate-100 p-4">
          <FormField label="Type">
            <Select
              value={type}
              onChange={(e) => {
                setType(e.target.value);
                setOffset(0);
              }}
              className="max-w-xs"
            >
              <option value="">All types</option>
              {TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </option>
              ))}
            </Select>
          </FormField>
        </div>

        {isLoading && <LoadingState />}
        {isError && <ErrorState message={(error as Error).message} />}
        {data && data.items.length === 0 && <EmptyState title="No transactions yet" />}

        {data && data.items.length > 0 && (
          <Table>
            <THead>
              <Tr>
                <Th>User</Th>
                <Th>Type</Th>
                <Th>Amount</Th>
                <Th>Balance After</Th>
                <Th>Reference</Th>
                <Th>Note</Th>
                <Th>When</Th>
              </Tr>
            </THead>
            <TBody>
              {data.items.map((entry) => (
                <Tr key={entry.id}>
                  <Td className="font-medium text-slate-900">
                    {entry.userName}
                    <span className="ml-1.5 text-xs font-normal text-slate-400">{entry.userPhone}</span>
                  </Td>
                  <Td>
                    <Badge tone={TYPE_TONE[entry.type] ?? 'slate'}>{entry.type}</Badge>
                  </Td>
                  <Td className={entry.amount >= 0 ? 'font-semibold text-emerald-600' : 'font-semibold text-red-600'}>
                    {entry.amount >= 0 ? '+' : ''}
                    {entry.amount.toLocaleString()}
                  </Td>
                  <Td>{entry.balanceAfter.toLocaleString()}</Td>
                  <Td className="text-xs text-slate-500">
                    {entry.referenceType ? `${entry.referenceType} #${entry.referenceId}` : '—'}
                  </Td>
                  <Td className="max-w-xs truncate text-slate-600">{entry.note ?? '—'}</Td>
                  <Td className="whitespace-nowrap text-xs text-slate-500">{new Date(entry.createdAt).toLocaleString()}</Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        )}
        {data && <Pagination total={data.total} limit={limit} offset={offset} onOffsetChange={setOffset} />}
      </Card>
    </div>
  );
}
