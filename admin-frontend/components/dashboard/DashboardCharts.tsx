'use client';

import { Bar, BarChart, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import type { DashboardData } from '@/lib/api/types';

const formatCredits = (value: number) => new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(value);

export default function DashboardCharts({
  today,
  markets,
}: {
  today: DashboardData['today'];
  markets: DashboardData['todayMarketPerformance'];
}) {
  const statusData = [
    { name: 'Pending', value: today.pending, color: '#f59e0b' },
    { name: 'Won', value: today.won, color: '#158671' },
    { name: 'Other', value: Math.max(today.simulations - today.pending - today.won, 0), color: '#cbd5e1' },
  ].filter((item) => item.value > 0);

  return (
    <div className="mb-6 grid gap-4 xl:grid-cols-5">
      <Card className="xl:col-span-3">
        <CardHeader>
          <CardTitle subtitle="Staked credits and payouts across active markets">Today’s Credit Flow</CardTitle>
        </CardHeader>
        <CardBody className="h-72 p-4 sm:p-5">
          {markets.length === 0 ? (
            <div className="flex h-full items-center justify-center text-sm text-slate-500">No market activity yet today.</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={markets} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                <XAxis dataKey="market" tickLine={false} axisLine={false} tick={{ fill: '#64748b', fontSize: 11 }} />
                <YAxis tickLine={false} axisLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={formatCredits} />
                <Tooltip
                  cursor={{ fill: '#f8fafc' }}
                  contentStyle={{ borderRadius: 6, borderColor: '#e2e8f0', fontSize: 12 }}
                  formatter={(value) => formatCredits(Number(value ?? 0))}
                />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
                <Bar dataKey="staked" name="Staked" fill="#158671" radius={[4, 4, 0, 0]} />
                <Bar dataKey="payout" name="Payout" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardBody>
      </Card>

      <Card className="xl:col-span-2">
        <CardHeader>
          <CardTitle subtitle="How today’s simulations are progressing">Simulation Status</CardTitle>
        </CardHeader>
        <CardBody className="h-72 p-4 sm:p-5">
          {statusData.length === 0 ? (
            <div className="flex h-full items-center justify-center text-sm text-slate-500">No simulations recorded today.</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={statusData} dataKey="value" nameKey="name" innerRadius="56%" outerRadius="78%" paddingAngle={3}>
                  {statusData.map((item) => <Cell key={item.name} fill={item.color} />)}
                </Pie>
                <Tooltip formatter={(value) => Number(value ?? 0).toLocaleString()} contentStyle={{ borderRadius: 6, borderColor: '#e2e8f0', fontSize: 12 }} />
                <Legend verticalAlign="bottom" iconType="circle" wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
