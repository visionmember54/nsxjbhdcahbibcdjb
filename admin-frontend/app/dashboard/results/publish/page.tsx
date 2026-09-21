'use client';

import PageHeader from '@/components/layout/PageHeader';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import PublishResultForm from '@/components/results/PublishResultForm';
import ResultsTable from '@/components/results/ResultsTable';
import { useResults } from '@/hooks/useResults';

export default function PublishResultPage() {
  const { data, isLoading, isError, error } = useResults({ status: 'Draft', limit: 10 });

  return (
    <div>
      <PageHeader icon="check" title="Publish Result" description="Declare Open/Close panna (or a direct ank/single result) and publish." />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle subtitle="Jodi only resolves once both Open and Close are published">New declaration</CardTitle>
          </CardHeader>
          <CardBody>
            <PublishResultForm />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Draft results awaiting publish</CardTitle>
          </CardHeader>
          <ResultsTable results={data?.items} isLoading={isLoading} isError={isError} errorMessage={(error as Error)?.message} />
        </Card>
      </div>
    </div>
  );
}
