'use client';

import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import { useGameStatistics } from '@/hooks/useReports';

export default function GameStatisticsPage() {
  const { data, isLoading, isError, error } = useGameStatistics();

  return (
    <div>
      <PageHeader icon="chart" title="Game Statistics" description="Credits staked, wins, payouts, and net credits by game type — computed live." />
      <Card>
        {isLoading && <LoadingState />}
        {isError && <ErrorState message={(error as Error).message} />}
        {data && data.length === 0 && <EmptyState title="No simulations yet" />}

        {data && data.length > 0 && (
          <Table>
            <THead>
              <Tr>
                <Th>Game type</Th>
                <Th>Credits Staked</Th>
                <Th>Wins</Th>
                <Th>Payouts</Th>
                <Th>Net Credits</Th>
              </Tr>
            </THead>
            <TBody>
              {data.map((row) => (
                <Tr key={row.gameType}>
                  <Td className="font-medium text-slate-900">{row.gameType}</Td>
                  <Td>{row.sales.toLocaleString()}</Td>
                  <Td>{row.winners}</Td>
                  <Td>{row.payout.toLocaleString()}</Td>
                  <Td className={row.profit >= 0 ? 'text-emerald-600' : 'text-red-600'}>{row.profit.toLocaleString()}</Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
