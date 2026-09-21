'use client';

import React, { useState } from 'react';
import { useStudents } from '@/hooks/useStudents';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, EmptyState } from '@/components/ui/States';
import { StatusBadge } from '@/components/ui/Badge';
import Link from 'next/link';
import Button from '@/components/ui/Button';
import UserExpandedDetails from './UserExpandedDetails';

export default function UsersOverview() {
  const { data, isLoading } = useStudents({ limit: 200 });
  const [expandedId, setExpandedId] = useState<number | null>(null);

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle subtitle="All registered users">Users</CardTitle>
        <Link href="/dashboard/students">
          <Button variant="secondary" size="sm">View All Users</Button>
        </Link>
      </CardHeader>

      {isLoading && <LoadingState />}
      {data?.items.length === 0 && <EmptyState title="No users yet" />}

      {data && data.items.length > 0 && (
        <div className="max-h-[600px] overflow-y-auto">
          <Table>
            <THead>
              <Tr>
                <Th>Name</Th>
                <Th>Phone</Th>
                <Th>Email</Th>
                <Th>Balance</Th>
                <Th>Status</Th>
              </Tr>
            </THead>
            <TBody>
              {data.items.map((s) => (
                <React.Fragment key={s.id}>
                  <Tr
                    className="cursor-pointer hover:bg-slate-50 transition-colors"
                    onClick={() => setExpandedId(expandedId === s.id ? null : s.id)}
                  >
                    <Td className="font-medium text-slate-900 flex items-center gap-2">
                      <span className="text-slate-400 w-4 inline-block text-center text-xs">
                        {expandedId === s.id ? '▼' : '▶'}
                      </span>
                      {s.name}
                    </Td>
                    <Td>{s.phone}</Td>
                    <Td>{s.email || '—'}</Td>
                    <Td>{s.balance.toLocaleString()}</Td>
                    <Td>
                      <StatusBadge status={s.status} />
                    </Td>
                  </Tr>
                  {expandedId === s.id && (
                    <Tr>
                      <Td colSpan={5} className="p-0 border-b border-slate-100">
                        <UserExpandedDetails studentId={s.id} />
                      </Td>
                    </Tr>
                  )}
                </React.Fragment>
              ))}
            </TBody>
          </Table>
        </div>
      )}
    </Card>
  );
}
