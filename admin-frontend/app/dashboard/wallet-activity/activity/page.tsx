'use client';

import { useMemo, useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, EmptyState } from '@/components/ui/States';
import { StatusBadge } from '@/components/ui/Badge';
import { FormField, Select } from '@/components/ui/Field';
import { useStudents } from '@/hooks/useStudents';
import { useCreditHistory } from '@/hooks/useCredits';
import { useSimulations } from '@/hooks/useSimulations';
import { useMarketsLookup } from '@/hooks/useMarketsLookup';

type Feed =
  | { kind: 'credit'; id: string; at: string; label: string; detail: string }
  | { kind: 'simulation'; id: string; at: string; label: string; detail: string; status: string };

export default function StudentActivityPage() {
  const { data: studentsPage } = useStudents({ limit: 100 });
  const [studentId, setStudentId] = useState<number | ''>('');
  const { byId } = useMarketsLookup();

  const { data: credits, isLoading: creditsLoading } = useCreditHistory(studentId || null, { limit: 25 });
  const { data: sims, isLoading: simsLoading } = useSimulations({ studentId: studentId || undefined, limit: 25 });

  const feed = useMemo<Feed[]>(() => {
    const items: Feed[] = [];
    credits?.items.forEach((c) =>
      items.push({
        kind: 'credit',
        id: `credit-${c.id}`,
        at: c.createdAt,
        label: c.type,
        detail: `${c.amount >= 0 ? '+' : ''}${c.amount} credits (balance ${c.balanceAfter})${c.note ? ` — ${c.note}` : ''}${!c.visibleToUser ? ' (Hidden from user)' : ''}`,
      })
    );
    sims?.items.forEach((s) =>
      items.push({
        kind: 'simulation',
        id: `sim-${s.id}`,
        at: s.createdAt,
        label: `${s.gameType} ${s.selection}`,
        detail: `${byId.get(s.marketId)?.name ?? `Market #${s.marketId}`} · ${s.simulatedCredits} credits staked`,
        status: s.status,
      })
    );
    return items.sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());
  }, [credits, sims, byId]);

  return (
    <div>
      <PageHeader icon="users" title="Activity" description="A merged recent feed of a user’s credit and simulation activity." />
      <Card>
        <div className="border-b border-slate-100 p-4">
          <FormField label="User">
            <Select value={studentId} onChange={(e) => setStudentId(e.target.value ? Number(e.target.value) : '')} className="max-w-sm">
              <option value="">Select a user…</option>
              {studentsPage?.items.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </Select>
          </FormField>
        </div>

        {!studentId && <EmptyState title="Select a user to view their activity" />}
        {studentId && (creditsLoading || simsLoading) && <LoadingState />}
        {studentId && !creditsLoading && !simsLoading && feed.length === 0 && <EmptyState title="No activity yet" />}

        {studentId && feed.length > 0 && (
          <Table>
            <THead>
              <Tr>
                <Th>When</Th>
                <Th>Type</Th>
                <Th>Detail</Th>
                <Th></Th>
              </Tr>
            </THead>
            <TBody>
              {feed.map((item) => (
                <Tr key={item.id}>
                  <Td>{new Date(item.at).toLocaleString()}</Td>
                  <Td className="font-medium text-slate-900">
                    {item.kind === 'credit' ? `Credit: ${item.label}` : `Simulation: ${item.label}`}
                  </Td>
                  <Td>{item.detail}</Td>
                  <Td>{item.kind === 'simulation' && <StatusBadge status={item.status} />}</Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
