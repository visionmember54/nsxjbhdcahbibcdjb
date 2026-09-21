'use client';

import { useState } from 'react';
import Link from 'next/link';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import { StatusBadge } from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Pagination from '@/components/ui/Pagination';
import { Input, Select } from '@/components/ui/Field';
import { useStudents, useUpdateStudent } from '@/hooks/useStudents';
import CreateStudentModal from '@/components/students/CreateStudentModal';

export default function StudentsPage() {
  const [offset, setOffset] = useState(0);
  const [createOpen, setCreateOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'active' | 'disabled' | ''>('');
  const limit = 20;
  const { data, isLoading, isError, error } = useStudents({ limit, offset, search, status: statusFilter || undefined });
  const updateStudent = useUpdateStudent();

  return (
    <div>
      <PageHeader
        icon="users"
        title="Users"
        description="Manage user accounts, access status, and virtual-credit balances."
        action={<Button onClick={() => setCreateOpen(true)}>+ New user</Button>}
      />
      <Card>
        <div className="grid gap-3 border-b border-slate-100 p-4 sm:grid-cols-2">
          <Input placeholder="Search name, phone, or email" value={search} onChange={(e) => { setSearch(e.target.value); setOffset(0); }} />
          <Select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value as 'active' | 'disabled' | ''); setOffset(0); }}>
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="disabled">Disabled</option>
          </Select>
        </div>
        {isLoading && <LoadingState />}
        {isError && <ErrorState message={(error as Error).message} />}
        {data && data.items.length === 0 && <EmptyState title="No users yet" />}

        {data && data.items.length > 0 && (
          <Table>
            <THead>
              <Tr>
                <Th>Name</Th>
                <Th>Phone</Th>
                <Th>Email</Th>
                <Th>Balance</Th>
                <Th>Status</Th>
                <Th></Th>
              </Tr>
            </THead>
            <TBody>
              {data.items.map((s) => (
                <Tr key={s.id}>
                  <Td className="font-medium text-slate-900"><Link href={`/dashboard/students/${s.id}`} className="hover:text-brand-600 hover:underline">{s.name}</Link></Td>
                  <Td>{s.phone}</Td>
                  <Td>{s.email || '—'}</Td>
                  <Td>{s.balance.toLocaleString()}</Td>
                  <Td>
                    <StatusBadge status={s.status} />
                  </Td>
                  <Td className="space-x-3">
                    <Link href={`/dashboard/wallet-activity/credits?studentId=${s.id}`} className="text-xs font-semibold text-brand-600 hover:underline">
                      Credits
                    </Link>
                    <button
                      className="text-xs font-semibold text-slate-500 hover:underline"
                      onClick={() => { const reason = window.prompt(`Optional reason for ${s.status === 'active' ? 'disabling' : 'enabling'} this user:`); updateStudent.mutate({ id: s.id, status: s.status === 'active' ? 'disabled' : 'active', reason: reason || undefined }); }}
                    >
                      {s.status === 'active' ? 'Disable' : 'Enable'}
                    </button>
                  </Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        )}
        {data && <Pagination total={data.total} limit={limit} offset={offset} onOffsetChange={setOffset} />}
      </Card>

      <CreateStudentModal open={createOpen} onClose={() => setCreateOpen(false)} />
    </div>
  );
}
