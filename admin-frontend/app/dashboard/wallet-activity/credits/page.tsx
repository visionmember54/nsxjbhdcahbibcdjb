'use client';

import { Suspense, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import PageHeader from '@/components/layout/PageHeader';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Pagination from '@/components/ui/Pagination';
import { FormField, Input, Select, Checkbox } from '@/components/ui/Field';
import type { Student } from '@/lib/api/types';
import { useStudents } from '@/hooks/useStudents';
import { useCreditHistory, useGrantCredits, useAdjustCredits, useResetCredits } from '@/hooks/useCredits';
import { usePermissions } from '@/hooks/usePermissions';

export default function LearningCreditsPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <LearningCreditsPageInner />
    </Suspense>
  );
}

function LearningCreditsPageInner() {
  const searchParams = useSearchParams();
  const initialStudentId = searchParams.get('studentId');
  const [search, setSearch] = useState('');
  const { data: studentsPage } = useStudents({ limit: 100, search });
  const [studentId, setStudentId] = useState<number | ''>(initialStudentId ? Number(initialStudentId) : '');
  const [offset, setOffset] = useState(0);
  const limit = 15;

  const [picked, setPicked] = useState<Student | null>(null);
  const selectedStudent = studentsPage?.items.find((s) => s.id === studentId) ?? (picked?.id === studentId ? picked : undefined);
  const { data: history, isLoading, isError, error } = useCreditHistory(studentId || null, { limit, offset });
  const { has } = usePermissions();
  const canManageCredits = has('credits.manage');

  return (
    <div>
      <PageHeader icon="users" title="Learning Credits" description="Grant, adjust, or reset a user’s virtual balance." />

      <Card className="mb-6">
        <CardBody>
          <FormField label="Find user">
            <Input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name, phone or email…"
              className="max-w-sm"
            />
          </FormField>
          <FormField label="User">
            <Select
              value={studentId}
              onChange={(e) => {
                const id = e.target.value ? Number(e.target.value) : '';
                setStudentId(id);
                setPicked(studentsPage?.items.find((s) => s.id === id) ?? null);
                setOffset(0);
              }}
              className="max-w-sm"
            >
              <option value="">Select a user…</option>
              {studentsPage?.items.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} — {s.balance.toLocaleString()} credits
                </option>
              ))}
            </Select>
          </FormField>
        </CardBody>
      </Card>

      {selectedStudent && (
        <>
          {canManageCredits && (
            <div key={selectedStudent.id} className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
              <GrantForm studentId={selectedStudent.id} />
              <AdjustForm studentId={selectedStudent.id} />
              <ResetForm studentId={selectedStudent.id} currentBalance={selectedStudent.balance} />
            </div>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Ledger history</CardTitle>
              <Badge tone="green">Balance: {selectedStudent.balance.toLocaleString()}</Badge>
            </CardHeader>

            {isLoading && <LoadingState />}
            {isError && <ErrorState message={(error as Error).message} />}
            {history && history.items.length === 0 && <EmptyState title="No ledger entries yet" />}

            {history && history.items.length > 0 && (
              <Table>
                <THead>
                  <Tr>
                    <Th>Type</Th>
                    <Th>Amount</Th>
                    <Th>Balance after</Th>
                    <Th>Visibility</Th>
                    <Th>Reference</Th>
                    <Th>Note</Th>
                    <Th>Date</Th>
                  </Tr>
                </THead>
                <TBody>
                  {history.items.map((h) => (
                    <Tr key={h.id}>
                      <Td className="font-medium text-slate-900">{h.type}</Td>
                      <Td className={h.amount >= 0 ? 'text-emerald-600' : 'text-red-600'}>
                        {h.amount >= 0 ? '+' : ''}
                        {h.amount.toLocaleString()}
                      </Td>
                      <Td>{h.balanceAfter.toLocaleString()}</Td>
                      <Td>{h.visibleToUser ? <Badge tone="green">Visible</Badge> : <Badge tone="slate">Hidden</Badge>}</Td>
                      <Td>{h.referenceType ?? '—'}</Td>
                      <Td className="max-w-xs truncate">{h.note ?? '—'}</Td>
                      <Td>{new Date(h.createdAt).toLocaleString()}</Td>
                    </Tr>
                  ))}
                </TBody>
              </Table>
            )}
            {history && <Pagination total={history.total} limit={limit} offset={offset} onOffsetChange={setOffset} />}
          </Card>
        </>
      )}
    </div>
  );
}

function GrantForm({ studentId }: { studentId: number }) {
  const grant = useGrantCredits();
  const [amount, setAmount] = useState('');
  const [note, setNote] = useState('');
  const [visibleToUser, setVisibleToUser] = useState(true);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Grant credits</CardTitle>
      </CardHeader>
      <CardBody>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            if (!note.trim()) return;
            await grant.mutateAsync({ studentId, amount: Number(amount), note: note.trim(), visibleToUser });
            setAmount('');
            setNote('');
            setVisibleToUser(true);
          }}
        >
          <FormField label="Amount">
            <Input type="number" min={1} required value={amount} onChange={(e) => setAmount(e.target.value)} />
          </FormField>
          <FormField label="Note (required)">
            <Input required value={note} onChange={(e) => setNote(e.target.value)} placeholder="Reason for this grant" />
          </FormField>
          <div className="mb-4">
            <Checkbox label="Visible to user in app history" checked={visibleToUser} onChange={(e) => setVisibleToUser(e.target.checked)} />
          </div>
          {grant.isError && <p className="mb-2 text-xs text-red-600">{(grant.error as Error).message}</p>}
          <Button type="submit" loading={grant.isPending} disabled={!note.trim()} className="w-full">
            Grant
          </Button>
        </form>
      </CardBody>
    </Card>
  );
}

function AdjustForm({ studentId }: { studentId: number }) {
  const adjust = useAdjustCredits();
  const [amount, setAmount] = useState('');
  const [note, setNote] = useState('');
  const [visibleToUser, setVisibleToUser] = useState(true);

  return (
    <Card>
      <CardHeader>
        <CardTitle subtitle="Signed: positive credits, negative debits">Adjust credits</CardTitle>
      </CardHeader>
      <CardBody>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            if (!note.trim()) return;
            await adjust.mutateAsync({ studentId, amount: Number(amount), note: note.trim(), visibleToUser });
            setAmount('');
            setNote('');
            setVisibleToUser(true);
          }}
        >
          <FormField label="Amount (+/-)">
            <Input type="number" required value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="-50 or 50" />
          </FormField>
          <FormField label="Note (required)">
            <Input required value={note} onChange={(e) => setNote(e.target.value)} placeholder="Reason for adjustment" />
          </FormField>
          <div className="mb-4">
            <Checkbox label="Visible to user in app history" checked={visibleToUser} onChange={(e) => setVisibleToUser(e.target.checked)} />
          </div>
          {adjust.isError && <p className="mb-2 text-xs text-red-600">{(adjust.error as Error).message}</p>}
          <Button type="submit" variant="secondary" loading={adjust.isPending} disabled={!note.trim()} className="w-full">
            Adjust
          </Button>
        </form>
      </CardBody>
    </Card>
  );
}

function ResetForm({ studentId, currentBalance }: { studentId: number; currentBalance: number }) {
  const reset = useResetCredits();
  const [newBalance, setNewBalance] = useState(String(currentBalance));
  const [note, setNote] = useState('');
  const [visibleToUser, setVisibleToUser] = useState(true);

  return (
    <Card>
      <CardHeader>
        <CardTitle subtitle="Sets balance to an exact value">Reset credits</CardTitle>
      </CardHeader>
      <CardBody>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            if (!note.trim()) return;
            await reset.mutateAsync({ studentId, new_balance: Number(newBalance), note: note.trim(), visibleToUser });
            setNote('');
            setVisibleToUser(true);
          }}
        >
          <FormField label="New balance">
            <Input type="number" min={0} required value={newBalance} onChange={(e) => setNewBalance(e.target.value)} />
          </FormField>
          <FormField label="Note (required)">
            <Input required value={note} onChange={(e) => setNote(e.target.value)} placeholder="Reason for this reset" />
          </FormField>
          <div className="mb-4">
            <Checkbox label="Visible to user in app history" checked={visibleToUser} onChange={(e) => setVisibleToUser(e.target.checked)} />
          </div>
          {reset.isError && <p className="mb-2 text-xs text-red-600">{(reset.error as Error).message}</p>}
          <Button type="submit" variant="danger" loading={reset.isPending} disabled={!note.trim()} className="w-full">
            Reset
          </Button>
        </form>
      </CardBody>
    </Card>
  );
}
