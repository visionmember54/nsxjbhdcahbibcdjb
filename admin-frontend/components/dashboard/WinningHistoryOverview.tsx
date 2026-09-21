'use client';

import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Link from 'next/link';
import { useSimulations } from '@/hooks/useSimulations';
import SimulationsTable from '@/components/simulations/SimulationsTable';

export default function WinningHistoryOverview() {
  // Fetch a larger batch so we can filter out the 'Won' ones on the client
  const { data, isLoading, isError, error } = useSimulations({ limit: 200 });

  const winningBids = data?.items?.filter((e) => e.status === 'Won') || [];

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle subtitle="Recent winning bids across all users and games">Winning History</CardTitle>
        <Link href="/dashboard/simulations">
          <Button variant="secondary" size="sm">View All Bids</Button>
        </Link>
      </CardHeader>
      <div className="max-h-[500px] overflow-y-auto">
        <SimulationsTable 
          entries={winningBids} 
          isLoading={isLoading} 
          isError={isError} 
          errorMessage={(error as Error)?.message} 
        />
      </div>
    </Card>
  );
}
