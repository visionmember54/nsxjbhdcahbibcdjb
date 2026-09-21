'use client';

import { useDashboard } from '@/hooks/useDashboard';
import PageHeader from '@/components/layout/PageHeader';
import StatTile from '@/components/ui/StatTile';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import DashboardCharts from '@/components/dashboard/DashboardCharts';
import GameInsights from '@/components/dashboard/GameInsights';
import UsersOverview from '@/components/dashboard/UsersOverview';
import WithdrawalRequestsOverview from '@/components/dashboard/WithdrawalRequestsOverview';
import BidsOverview from '@/components/dashboard/BidsOverview';
import WalletTransactionsOverview from '@/components/dashboard/WalletTransactionsOverview';
import WinningHistoryOverview from '@/components/dashboard/WinningHistoryOverview';

export default function OverviewPage() {
  const { data, isLoading, isError, error } = useDashboard();

  return (
    <div>
      <PageHeader icon="home" title="Overview" description="A live snapshot of users, markets, results, and today’s virtual-credit activity." />

      {isLoading && <LoadingState />}
      {isError && <ErrorState message={(error as Error).message} />}

      {data && (
        <>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">All-time totals, across every game and market</p>
          <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-5">
            <StatTile
              label="Active Users"
              value={data.stats.activeUsers}
              hint={`${data.stats.totalUsers} total registered`}
              icon="users"
              tone="blue"
            />
            <StatTile label="Games Played" value={data.stats.totalSimulations.toLocaleString()} hint={`${data.stats.totalWon} won · ${data.stats.totalLost} lost · ${data.stats.totalPending} pending`} icon="play" tone="purple" />
            <StatTile label="Credits In (Staked)" value={data.stats.totalCreditsStaked.toLocaleString()} icon="coin" tone="emerald" />
            <StatTile label="Credits Out (Paid)" value={data.stats.totalCreditsPaidOut.toLocaleString()} icon="coin" tone="red" />
            <StatTile
              label="Net (In − Out)"
              value={data.stats.totalNetCredits.toLocaleString()}
              valueClassName={data.stats.totalNetCredits >= 0 ? 'text-emerald-600' : 'text-red-600'}
              icon="chart"
              tone={data.stats.totalNetCredits >= 0 ? 'emerald' : 'red'}
            />
          </div>

          <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatTile label="Open Markets" value={data.stats.openMarkets} icon="market" tone="emerald" />
            <StatTile label="Pending Results" value={data.stats.pendingResults} icon="clock" tone="amber" />
            <StatTile label="Active Starline Slots" value={data.stats.activeStarlineSlots} icon="sliders" tone="slate" />
            <StatTile label="Total Users" value={data.stats.totalUsers} icon="users" tone="slate" />
          </div>

          <UsersOverview />

          <WithdrawalRequestsOverview />

          <BidsOverview />

          <WalletTransactionsOverview />

          <WinningHistoryOverview />

          <div className="mb-6 grid gap-4 xl:grid-cols-5">
            <Card className="xl:col-span-3">
              <CardHeader>
                <CardTitle subtitle={`Activity for ${data.today.date}`}>Today’s Performance</CardTitle>
              </CardHeader>
              <CardBody>
                <div className="grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-4">
                  <div><p className="text-xs font-medium text-slate-500">Credits staked</p><p className="mt-1 text-xl font-bold text-slate-950">{data.today.staked.toLocaleString()}</p></div>
                  <div><p className="text-xs font-medium text-slate-500">Payouts</p><p className="mt-1 text-xl font-bold text-slate-950">{data.today.payout.toLocaleString()}</p></div>
                  <div><p className="text-xs font-medium text-slate-500">Net credits</p><p className={`mt-1 text-xl font-bold ${data.today.net >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{data.today.net.toLocaleString()}</p></div>
                  <div><p className="text-xs font-medium text-slate-500">Simulations</p><p className="mt-1 text-xl font-bold text-slate-950">{data.today.simulations.toLocaleString()}</p></div>
                </div>
              </CardBody>
            </Card>
            <Card className="xl:col-span-2">
              <CardHeader><CardTitle subtitle="Items that may need attention">Today’s Status</CardTitle></CardHeader>
              <CardBody className="grid grid-cols-2 gap-4">
                <div><p className="text-xs text-slate-500">Pending simulations</p><p className="mt-1 text-lg font-bold text-amber-600">{data.today.pending}</p></div>
                <div><p className="text-xs text-slate-500">Winning simulations</p><p className="mt-1 text-lg font-bold text-emerald-600">{data.today.won}</p></div>
                <div><p className="text-xs text-slate-500">Results published</p><p className="mt-1 text-lg font-bold text-slate-950">{data.today.publishedResults}</p></div>
                <div><p className="text-xs text-slate-500">New users</p><p className="mt-1 text-lg font-bold text-slate-950">{data.today.newUsers}</p></div>
              </CardBody>
            </Card>
          </div>

          <DashboardCharts today={data.today} markets={data.todayMarketPerformance} />

          <GameInsights />

          <div className="mb-6 grid gap-4 xl:grid-cols-3">
            <Card><CardHeader><CardTitle subtitle="By submitted simulations">Most Popular Market</CardTitle></CardHeader><CardBody><p className="text-lg font-bold text-slate-950">{data.popularMarket?.name ?? '—'}</p><p className="text-xs text-slate-500">{data.popularMarket?.count ?? 0} simulations</p></CardBody></Card>
            <Card><CardHeader><CardTitle subtitle="By submitted simulations">Most Popular Game</CardTitle></CardHeader><CardBody><p className="text-lg font-bold text-slate-950">{data.popularGame?.code ?? '—'}</p><p className="text-xs text-slate-500">{data.popularGame?.count ?? 0} simulations</p></CardBody></Card>
            <Card><CardHeader><CardTitle subtitle="Markets awaiting opening">Upcoming Markets</CardTitle></CardHeader><CardBody>{data.upcomingMarkets.length ? <ul className="space-y-1 text-sm text-slate-700">{data.upcomingMarkets.map((market) => <li key={market.id}>{market.name} <span className="text-slate-400">{market.openingTime ?? 'time unset'}</span></li>)}</ul> : <p className="text-sm text-slate-500">None scheduled.</p>}</CardBody></Card>
          </div>

          <Card className="mb-6"><CardHeader><CardTitle subtitle="Latest configuration and operating changes">Recent Admin Actions</CardTitle></CardHeader><CardBody>{data.recentAdminActions.length ? <ul className="space-y-2">{data.recentAdminActions.map((item) => <li key={item.id} className="text-sm"><span className="font-semibold text-slate-900">{item.actor}</span> <span className="text-slate-600">{item.details}</span><span className="ml-2 text-xs text-slate-400">{item.createdAt}</span></li>)}</ul> : <p className="text-sm text-slate-500">No actions recorded yet.</p>}</CardBody></Card>

          <Card className="mb-6">
            <CardHeader>
              <CardTitle subtitle="Today’s activity, grouped by market">Today by Market</CardTitle>
            </CardHeader>
            {data.todayMarketPerformance.length === 0 ? (
              <EmptyState title="No activity today" hint="Today’s market performance will appear as users submit simulations." />
            ) : (
              <Table>
                <THead><Tr><Th>Market</Th><Th>Simulations</Th><Th>Credits Staked</Th><Th>Payouts</Th><Th>Net Credits</Th></Tr></THead>
                <TBody>
                  {data.todayMarketPerformance.map((row) => (
                    <Tr key={row.marketId}>
                      <Td className="font-medium text-slate-900">{row.market}</Td>
                      <Td>{row.simulations}</Td><Td>{row.staked.toLocaleString()}</Td><Td>{row.payout.toLocaleString()}</Td>
                      <Td className={row.net >= 0 ? 'font-semibold text-emerald-600' : 'font-semibold text-red-600'}>{row.net.toLocaleString()}</Td>
                    </Tr>
                  ))}
                </TBody>
              </Table>
            )}
          </Card>

          <Card>
            <CardHeader>
              <CardTitle subtitle="Credits staked, winning simulations, payouts, and net credits by market">Market Statistics</CardTitle>
            </CardHeader>
            {data.marketStatistics.length === 0 ? (
              <EmptyState title="No simulations yet" hint="Statistics appear once users start submitting selections." />
            ) : (
              <Table>
                <THead>
                  <Tr>
                    <Th>Market</Th>
                    <Th>Credits Staked</Th>
                    <Th>Wins</Th>
                    <Th>Payouts</Th>
                    <Th>Net Credits</Th>
                  </Tr>
                </THead>
                <TBody>
                  {data.marketStatistics.map((row) => (
                    <Tr key={row.marketId}>
                      <Td className="font-medium text-slate-900">{row.market}</Td>
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
        </>
      )}
    </div>
  );
}
