'use client';

import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, EmptyState } from '@/components/ui/States';
import Button from '@/components/ui/Button';
import Link from 'next/link';
import { useGlobalCreditLedger } from '@/hooks/useCreditLedger';

export default function WalletTransactionsOverview() {
  const { data, isLoading, isError, error } = useGlobalCreditLedger({ limit: 50 });

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle subtitle="Full statement of every credit ledger activity">Wallet Transactions</CardTitle>
        <Link href="/dashboard/wallet-activity/transactions">
          <Button variant="secondary" size="sm">View All Transactions</Button>
        </Link>
      </CardHeader>

      {isLoading && <LoadingState />}
      {isError && <div className="p-4 text-red-600 text-sm">{(error as Error).message}</div>}
      {!isLoading && !isError && data?.items.length === 0 && (
        <EmptyState title="No transactions yet" hint="Ledger activities will appear here." />
      )}

      {!isLoading && !isError && data && data.items.length > 0 && (
        <div className="max-h-[500px] overflow-y-auto">
          <Table>
            <THead>
              <Tr>
                <Th>User</Th>
                <Th>Type</Th>
                <Th>Amount</Th>
                <Th>Balance After</Th>
                <Th>Note / Reference</Th>
                <Th>Date</Th>
              </Tr>
            </THead>
            <TBody>
              {data.items.map((t) => (
                <Tr key={t.id}>
                  <Td className="font-medium text-slate-900">
                    {t.userName}
                    <span className="block text-xs font-normal text-slate-400">{t.userPhone}</span>
                  </Td>
                  <Td>
                    <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
                      {t.type}
                    </span>
                  </Td>
                  <Td className={`font-bold ${t.amount > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                    {t.amount > 0 ? '+' : ''}{t.amount.toLocaleString()}
                  </Td>
                  <Td className="text-slate-600">{t.balanceAfter.toLocaleString()}</Td>
                  <Td className="max-w-[200px] text-xs text-slate-500">
                    {t.note && <div className="truncate mb-1" title={t.note}>{t.note}</div>}
                    {t.referenceType && (
                      <div className="font-mono text-[10px] text-slate-400 uppercase">
                        {t.referenceType} #{t.referenceId}
                      </div>
                    )}
                    {!t.note && !t.referenceType && '—'}
                  </Td>
                  <Td className="whitespace-nowrap text-xs text-slate-500">
                    {new Date(t.createdAt).toLocaleString()}
                  </Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        </div>
      )}
    </Card>
  );
}
