'use client';

import { useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import Pagination from '@/components/ui/Pagination';
import { useAuditLogs } from '@/hooks/useAuditLogs';

export default function AuditLogsPage() {
  const [offset, setOffset] = useState(0);
  const limit = 25;
  const { data, isLoading, isError, error } = useAuditLogs({ limit, offset });

  return (
    <div>
      <PageHeader icon="cog" title="Audit Logs" description="Append-only log of every admin action." />
      <Card>
        {isLoading && <LoadingState />}
        {isError && <ErrorState message={(error as Error).message} />}
        {data && data.items.length === 0 && <EmptyState title="No activity yet" />}

        {data && data.items.length > 0 && (
          <Table>
            <THead>
              <Tr>
                <Th>Actor</Th>
                <Th>Action</Th>
                <Th>Details</Th>
                <Th>When</Th>
              </Tr>
            </THead>
            <TBody>
              {data.items.map((log) => (
                <Tr key={log.id}>
                  <Td className="font-medium text-slate-900">{log.actor}</Td>
                  <Td className="font-mono text-xs">{log.action}</Td>
                  <Td className="max-w-lg">{log.details}</Td>
                  <Td>{log.createdAt}</Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        )}
        {data && <Pagination total={data.total} limit={limit} offset={offset} onOffsetChange={setOffset} />}
      </Card>
    </div>
  );
}
