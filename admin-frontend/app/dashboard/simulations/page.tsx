'use client';

import { useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Pagination from '@/components/ui/Pagination';
import SimulationsTable from '@/components/simulations/SimulationsTable';
import BulkSimulationForm from '@/components/simulations/BulkSimulationForm';
import { useSimulations } from '@/hooks/useSimulations';

export default function AllSimulationsPage() {
  const [offset, setOffset] = useState(0);
  const [modalOpen, setModalOpen] = useState(false);
  const limit = 20;
  const { data, isLoading, isError, error } = useSimulations({ limit, offset });

  return (
    <div>
      <PageHeader
        icon="play"
        title="All Simulations"
        description="Every selection submitted, single or bulk, admin-entered or app-submitted."
        action={<Button onClick={() => setModalOpen(true)}>+ New bulk submission</Button>}
      />
      <Card>
        <SimulationsTable entries={data?.items} isLoading={isLoading} isError={isError} errorMessage={(error as Error)?.message} />
        {data && <Pagination total={data.total} limit={limit} offset={offset} onOffsetChange={setOffset} />}
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Submit a bulk selection batch" maxWidth="max-w-2xl">
        <BulkSimulationForm onDone={() => setModalOpen(false)} />
      </Modal>
    </div>
  );
}
