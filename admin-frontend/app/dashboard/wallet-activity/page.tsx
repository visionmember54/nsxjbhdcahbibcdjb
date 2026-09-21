'use client';

import Link from 'next/link';
import PageHeader from '@/components/layout/PageHeader';
import StatTile from '@/components/ui/StatTile';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import Badge from '@/components/ui/Badge';
import { Icon } from '@/components/layout/icons';
import { useDashboard } from '@/hooks/useDashboard';
import { useCreditRequests } from '@/hooks/useCreditRequests';
import { useGlobalCreditLedger } from '@/hooks/useCreditLedger';

const TYPE_TONE: Record<string, 'green' | 'blue' | 'purple' | 'amber' | 'slate'> = {
  grant: 'green',
  adjustment: 'blue',
  reset: 'purple',
  stake: 'slate',
  payout: 'amber',
};

export default function WalletActivityOverviewPage() {
  const { data: dashboard } = useDashboard();
  const { data: requests } = useCreditRequests({ limit: 100 });
  const { data: ledger, isLoading, isError, error } = useGlobalCreditLedger({ limit: 8 });

  const pendingCount = (requests?.items ?? []).filter((r) => r.status === 'Pending').length;

  return (
    <div>
      <PageHeader
        icon="coin"
        title="Wallet Activity"
        description="Every virtual credit request and ledger movement, across every user, in one place."
        action={
          <Link
            href="/dashboard/wallet-activity/credit-requests"
            className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-b from-brand-500 to-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-glow transition-all hover:from-brand-400 hover:to-brand-500 active:scale-[0.98]"
          >
            Review requests
          </Link>
        }
      />

      {dashboard && (
        <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatTile
            label="Pending Requests"
            value={pendingCount}
            hint={pendingCount > 0 ? 'Waiting on a decision' : 'All caught up'}
            icon="clock"
            tone={pendingCount > 0 ? 'amber' : 'emerald'}
          />
          <StatTile label="Credits In (Staked)" value={dashboard.stats.totalCreditsStaked.toLocaleString()} icon="coin" tone="emerald" />
          <StatTile label="Credits Out (Paid)" value={dashboard.stats.totalCreditsPaidOut.toLocaleString()} icon="coin" tone="red" />
          <StatTile
            label="Net (In − Out)"
            value={dashboard.stats.totalNetCredits.toLocaleString()}
            valueClassName={dashboard.stats.totalNetCredits >= 0 ? 'text-emerald-600' : 'text-red-600'}
            icon="chart"
            tone={dashboard.stats.totalNetCredits >= 0 ? 'emerald' : 'red'}
          />
        </div>
      )}

      <div className="mb-6 grid gap-4 lg:grid-cols-3">
        <Link
          href="/dashboard/students/credit-requests"
          className="group flex items-center gap-3 rounded-xl border border-slate-200/80 bg-white p-4 shadow-soft transition-all hover:-translate-y-0.5 hover:shadow-card"
        >
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
            <Icon name="coin" className="h-5 w-5" />
          </span>
          <div>
            <p className="text-sm font-semibold text-slate-900">Credit Requests</p>
            <p className="text-xs text-slate-500">Approve or reject user top-up asks</p>
          </div>
        </Link>
        <Link
          href="/dashboard/wallet-activity/credits"
          className="group flex items-center gap-3 rounded-xl border border-slate-200/80 bg-white p-4 shadow-soft transition-all hover:-translate-y-0.5 hover:shadow-card"
        >
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
            <Icon name="sliders" className="h-5 w-5" />
          </span>
          <div>
            <p className="text-sm font-semibold text-slate-900">Learning Credits</p>
            <p className="text-xs text-slate-500">Grant, adjust, or reset a user&rsquo;s balance</p>
          </div>
        </Link>
        <Link
          href="/dashboard/wallet-activity/transactions"
          className="group flex items-center gap-3 rounded-xl border border-slate-200/80 bg-white p-4 shadow-soft transition-all hover:-translate-y-0.5 hover:shadow-card"
        >
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
            <Icon name="chart" className="h-5 w-5" />
          </span>
          <div>
            <p className="text-sm font-semibold text-slate-900">All Transactions</p>
            <p className="text-xs text-slate-500">The full ledger, every user, one feed</p>
          </div>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle subtitle="The 8 most recent credit movements, across every user">Recent Transactions</CardTitle>
          <Link href="/dashboard/wallet-activity/transactions" className="text-xs font-semibold text-brand-600 hover:underline">
            View all →
          </Link>
        </CardHeader>
        {isLoading && <LoadingState />}
        {isError && <ErrorState message={(error as Error).message} />}
        {ledger && ledger.items.length === 0 && <EmptyState title="No credit movement yet" />}
        {ledger && ledger.items.length > 0 && (
          <Table>
            <THead>
              <Tr>
                <Th>User</Th>
                <Th>Type</Th>
                <Th>Amount</Th>
                <Th>Balance After</Th>
                <Th>When</Th>
              </Tr>
            </THead>
            <TBody>
              {ledger.items.map((entry) => (
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
                  <Td className="whitespace-nowrap text-xs text-slate-500">{new Date(entry.createdAt).toLocaleString()}</Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
