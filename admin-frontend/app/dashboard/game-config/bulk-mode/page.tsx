'use client';

import { useMemo, useState } from 'react';
import { useAllGameTypeConfigs } from '@/hooks/useGameTypeConfigs';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { Select } from '@/components/ui/Field';
import GameConfigTable from '@/components/gameConfig/GameConfigTable';

export default function BulkModePage() {
  const { data, isLoading, isError, error } = useAllGameTypeConfigs();
  const [filter, setFilter] = useState<'all' | 'bulk_on' | 'bulk_off'>('all');

  const filtered = useMemo(() => {
    if (!data) return data;
    if (filter === 'bulk_on') return data.filter((c) => c.bulk_enabled);
    if (filter === 'bulk_off') return data.filter((c) => !c.bulk_enabled);
    return data;
  }, [data, filter]);

  return (
    <div>
      <PageHeader
        icon="sliders"
        title="Bulk Mode"
        description="bulk_enabled, max_bulk_selections, same/individual amount, and duplicate-selection rules across every market/game-type combination."
      />
      <Card>
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <h2 className="text-sm font-semibold text-slate-900">Bulk configuration</h2>
          <Select value={filter} onChange={(e) => setFilter(e.target.value as typeof filter)} className="w-44">
            <option value="all">All</option>
            <option value="bulk_on">Bulk enabled</option>
            <option value="bulk_off">Bulk disabled</option>
          </Select>
        </div>
        <div className="p-5">
          <GameConfigTable configs={filtered} isLoading={isLoading} isError={isError} errorMessage={(error as Error)?.message} />
        </div>
      </Card>
    </div>
  );
}
