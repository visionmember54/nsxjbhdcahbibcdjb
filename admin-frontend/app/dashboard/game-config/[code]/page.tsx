'use client';

import { useParams } from 'next/navigation';
import { useGameTypeConfigsByCode } from '@/hooks/useGameTypeConfigs';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import GameConfigTable from '@/components/gameConfig/GameConfigTable';

const LABELS: Record<string, string> = {
  SINGLE: 'Single',
  JODI: 'Jodi',
  SINGLE_PANNA: 'Single Panna',
  DOUBLE_PANNA: 'Double Panna',
  TRIPLE_PANNA: 'Triple Panna',
  HALF_SANGAM: 'Half Sangam',
  FULL_SANGAM: 'Full Sangam',
};

export default function GameConfigByCodePage() {
  const params = useParams<{ code: string }>();
  const code = params.code.toUpperCase();
  const { data, isLoading, isError, error } = useGameTypeConfigsByCode(code);

  return (
    <div>
      <PageHeader icon="sliders" title={LABELS[code] ?? code} description={`Where ${LABELS[code] ?? code} is enabled, and its per-market configuration.`} />
      <Card>
        <div className="border-b border-slate-100 px-5 py-4">
          <h2 className="text-sm font-semibold text-slate-900">Markets with {LABELS[code] ?? code} enabled</h2>
        </div>
        <div className="p-5">
          <GameConfigTable configs={data} isLoading={isLoading} isError={isError} errorMessage={(error as Error)?.message} />
        </div>
      </Card>
    </div>
  );
}
