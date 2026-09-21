'use client';

import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import ResultsTable from '@/components/results/ResultsTable';
import { useResults } from '@/hooks/useResults';

export default function PendingResultsPage() {
  const { data, isLoading, isError, error } = useResults({ status: 'Draft', limit: 50 });

  return (
    <div>
      <PageHeader icon="check" title="Pending" description="Draft results not yet published." />
      <Card>
        <ResultsTable results={data?.items} isLoading={isLoading} isError={isError} errorMessage={(error as Error)?.message} />
      </Card>
    </div>
  );
}
