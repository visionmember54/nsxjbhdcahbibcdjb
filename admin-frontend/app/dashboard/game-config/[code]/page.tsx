'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { useGameTypeConfigsByCode } from '@/hooks/useGameTypeConfigs';
import { useGameTypes } from '@/hooks/useGameTypes';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import GameConfigTable from '@/components/gameConfig/GameConfigTable';
import BulkApplyGameTypeConfigModal from '@/components/gameConfig/BulkApplyGameTypeConfigModal';
import Button from '@/components/ui/Button';

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
  const { data: gameTypes } = useGameTypes();
  const gameTypeId = gameTypes?.find((gt) => gt.code === code)?.id;
  const [bulkOpen, setBulkOpen] = useState(false);

  return (
    <div>
      <PageHeader
        icon="sliders"
        title={LABELS[code] ?? code}
        description={`Where ${LABELS[code] ?? code} is enabled, and its per-market configuration.`}
        action={gameTypeId ? <Button onClick={() => setBulkOpen(true)}>Apply to markets</Button> : undefined}
      />
      <Card>
        <div className="border-b border-slate-100 px-5 py-4">
          <h2 className="text-sm font-semibold text-slate-900">Markets with {LABELS[code] ?? code} enabled</h2>
        </div>
        <div className="p-5">
          <GameConfigTable configs={data} isLoading={isLoading} isError={isError} errorMessage={(error as Error)?.message} />
        </div>
      </Card>
      {gameTypeId && (
        <BulkApplyGameTypeConfigModal open={bulkOpen} onClose={() => setBulkOpen(false)} gameTypeId={gameTypeId} gameTypeLabel={LABELS[code] ?? code} />
      )}
    </div>
  );
}
