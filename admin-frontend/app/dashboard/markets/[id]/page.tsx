'use client';

import { useParams } from 'next/navigation';
import { useMarket, useUpdateMarketStatus } from '@/hooks/useMarkets';
import PageHeader from '@/components/layout/PageHeader';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { StatusBadge } from '@/components/ui/Badge';
import { LoadingState, ErrorState } from '@/components/ui/States';
import Button from '@/components/ui/Button';
import GameTypeConfigsPanel from '@/components/markets/GameTypeConfigsPanel';
import RatesPanel from '@/components/markets/RatesPanel';
import StarlineSlotsPanel from '@/components/markets/StarlineSlotsPanel';

const NEXT_STATUSES: Record<string, string[]> = {
  UPCOMING: ['OPEN', 'SUSPENDED'],
  OPEN: ['CLOSED', 'SUSPENDED'],
  CLOSED: ['RESULT_PENDING', 'OPEN', 'SUSPENDED'],
  RESULT_PENDING: ['RESULT_PUBLISHED', 'SUSPENDED'],
  RESULT_PUBLISHED: ['UPCOMING', 'SUSPENDED'],
  SUSPENDED: ['UPCOMING'],
};

export default function MarketDetailPage() {
  const params = useParams<{ id: string }>();
  const marketId = Number(params.id);
  const { data: market, isLoading, isError, error } = useMarket(marketId);
  const updateStatus = useUpdateMarketStatus();

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState message={(error as Error).message} />;
  if (!market) return null;

  const isStarline = market.category === 'STARLINE';
  const nextStatuses = NEXT_STATUSES[market.status] ?? [];

  return (
    <div>
      <PageHeader icon="market" title={market.name} description={`${market.category} market`} />

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Market status</CardTitle>
          <StatusBadge status={market.status} />
        </CardHeader>
        <CardBody>
          <div className="mb-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <div>
              <p className="text-xs text-slate-500">Opening</p>
              <p className="font-medium text-slate-800">{market.opening_time ?? '—'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Closing</p>
              <p className="font-medium text-slate-800">{market.closing_time ?? '—'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Cutoff</p>
              <p className="font-medium text-slate-800">{market.cutoff_time ?? market.closing_time ?? '—'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Result</p>
              <p className="font-medium text-slate-800">{market.result_time ?? '—'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Timezone</p>
              <p className="font-medium text-slate-800">{market.timezone}</p>
            </div>
          </div>

          {nextStatuses.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-semibold text-slate-500">Transition to:</p>
              <div className="flex flex-wrap gap-2">
                {nextStatuses.map((s) => (
                  <Button
                    key={s}
                    size="sm"
                    variant="secondary"
                    loading={updateStatus.isPending}
                    onClick={() => updateStatus.mutate({ id: marketId, status: s })}
                  >
                    {s}
                  </Button>
                ))}
              </div>
            </div>
          )}
          {updateStatus.isError && <p className="mt-2 text-xs text-red-600">{(updateStatus.error as Error).message}</p>}
        </CardBody>
      </Card>

      {isStarline ? (
        <Card>
          <CardBody>
            <StarlineSlotsPanel marketId={marketId} />
          </CardBody>
        </Card>
      ) : (
        <div className="space-y-6">
          <Card>
            <CardBody>
              <GameTypeConfigsPanel marketId={marketId} />
            </CardBody>
          </Card>
          <Card>
            <CardBody>
              <RatesPanel marketId={marketId} />
            </CardBody>
          </Card>
        </div>
      )}
    </div>
  );
}
