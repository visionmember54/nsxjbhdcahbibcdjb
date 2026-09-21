'use client';

import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Link from 'next/link';
import { useSimulations } from '@/hooks/useSimulations';
import SimulationsTable from '@/components/simulations/SimulationsTable';

export default function BidsOverview() {
  const { data, isLoading, isError, error } = useSimulations({ limit: 50 });

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle subtitle="Recent bids placed across all games">Bid History</CardTitle>
        <Link href="/dashboard/simulations">
          <Button variant="secondary" size="sm">View All Bids</Button>
        </Link>
      </CardHeader>
      <div className="max-h-[500px] overflow-y-auto">
        <SimulationsTable 
          entries={data?.items} 
          isLoading={isLoading} 
          isError={isError} 
          errorMessage={(error as Error)?.message} 
        />
      </div>
    </Card>
  );
}
