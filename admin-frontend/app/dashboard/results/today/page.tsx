'use client';

import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import ResultsTable from '@/components/results/ResultsTable';
import { useResults } from '@/hooks/useResults';
import { todayLocalIso } from '@/lib/date';

export default function TodaysResultsPage() {
  const today = todayLocalIso();
  const { data, isLoading, isError, error } = useResults({ dateFrom: today, dateTo: today, limit: 50 });

  return (
    <div>
      <PageHeader icon="check" title="Today's Results" description={today} />
      <Card>
        <ResultsTable results={data?.items} isLoading={isLoading} isError={isError} errorMessage={(error as Error)?.message} />
      </Card>
    </div>
  );
}
