'use client';

import { useGameTypeConfigsByCode } from '@/hooks/useGameTypeConfigs';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import GameConfigTable from '@/components/gameConfig/GameConfigTable';

export default function OpenClosePage() {
  const open = useGameTypeConfigsByCode('OPEN');
  const close = useGameTypeConfigsByCode('CLOSE');
  const openClose = useGameTypeConfigsByCode('OPEN_CLOSE');

  const isLoading = open.isLoading || close.isLoading || openClose.isLoading;
  const isError = open.isError || close.isError || openClose.isError;
  const combined = [...(open.data ?? []), ...(close.data ?? []), ...(openClose.data ?? [])];

  return (
    <div>
      <PageHeader
        icon="sliders"
        title="Open / Close"
        description="Per-market Open, Close, and combined Open+Close ank configuration."
      />
      <Card>
        <div className="border-b border-slate-100 px-5 py-4">
          <h2 className="text-sm font-semibold text-slate-900">Open / Close configuration</h2>
        </div>
        <div className="p-5">
          <GameConfigTable
            configs={isLoading ? undefined : combined}
            isLoading={isLoading}
            isError={isError}
            errorMessage="Failed to load Open/Close configuration"
          />
        </div>
      </Card>
    </div>
  );
}
