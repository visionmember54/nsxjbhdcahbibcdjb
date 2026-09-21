'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, EmptyState } from '@/components/ui/States';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import { useCreditRequests, useApproveCreditRequest, useRejectCreditRequest } from '@/hooks/useCreditRequests';
import { usePermissions } from '@/hooks/usePermissions';
import type { CreditRequest } from '@/lib/api/types';
import Link from 'next/link';

const STATUS_TONE: Record<CreditRequest['status'], 'amber' | 'green' | 'red'> = {
  Pending: 'amber',
  Approved: 'green',
  Rejected: 'red',
};

export default function WithdrawalRequestsOverview() {
  const { data, isLoading } = useCreditRequests({ limit: 50 });
  const approve = useApproveCreditRequest();
  const reject = useRejectCreditRequest();
  const { has } = usePermissions();
  const canManage = has('credits.manage');

  const [noteDrafts, setNoteDrafts] = useState<Record<number, string>>({});

  // Filter only withdrawal requests
  const withdrawals = (data?.items ?? []).filter((r) => r.requestType.toLowerCase() === 'withdrawal');

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle subtitle="Recent withdrawal requests and payment updates">Withdrawal History</CardTitle>
        <Link href="/dashboard/wallet-activity/credit-requests">
          <Button variant="secondary" size="sm">View All Requests</Button>
        </Link>
      </CardHeader>

      {isLoading && <LoadingState />}
      {!isLoading && withdrawals.length === 0 && (
        <EmptyState title="No withdrawal requests" hint="Pending withdrawal requests will appear here." />
      )}

      {!isLoading && withdrawals.length > 0 && (
        <div className="max-h-[500px] overflow-y-auto">
          <Table>
            <THead>
              <Tr>
                <Th>User</Th>
                <Th>Amount</Th>
                <Th>Payment Details</Th>
                <Th>Status</Th>
                <Th>Requested At</Th>
                {canManage && <Th>Actions</Th>}
              </Tr>
            </THead>
            <TBody>
              {withdrawals.map((r) => (
                <Tr key={r.id}>
                  <Td className="font-medium text-slate-900">
                    {r.userName}
                    <span className="block text-xs font-normal text-slate-400">{r.userPhone}</span>
                  </Td>
                  <Td className="font-semibold text-brand-700">
                    -{r.requestedAmount.toLocaleString()}
                  </Td>
                  <Td className="max-w-[200px] text-xs text-slate-600 space-y-1">
                    {r.paymentDetails && <div><span className="font-semibold">To:</span> {r.paymentDetails}</div>}
                    {r.reason && <div className="truncate" title={r.reason}>{r.reason}</div>}
                    {!r.paymentDetails && !r.reason && '—'}
                  </Td>
                  <Td>
                    <Badge tone={STATUS_TONE[r.status]}>{r.status}</Badge>
                    {r.status !== 'Pending' && r.adminNote && (
                      <p className="mt-1 max-w-[14rem] truncate text-[11px] text-slate-400" title={r.adminNote}>
                        &ldquo;{r.adminNote}&rdquo;
                      </p>
                    )}
                  </Td>
                  <Td className="whitespace-nowrap text-xs text-slate-500">{new Date(r.createdAt).toLocaleString()}</Td>
                  {canManage && (
                    <Td>
                      {r.status === 'Pending' ? (
                        <div className="flex flex-col gap-2 min-w-[140px]">
                          <input
                            className="w-full rounded-md border border-slate-200 px-2 py-1 text-xs placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
                            placeholder="Optional note"
                            value={noteDrafts[r.id] ?? ''}
                            onChange={(e) => setNoteDrafts((prev) => ({ ...prev, [r.id]: e.target.value }))}
                          />
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              className="flex-1 justify-center"
                              loading={approve.isPending}
                              onClick={() => approve.mutate({ id: r.id, adminNote: noteDrafts[r.id] })}
                            >
                              Accept
                            </Button>
                            <Button
                              size="sm"
                              variant="danger"
                              className="flex-1 justify-center"
                              loading={reject.isPending}
                              onClick={() => reject.mutate({ id: r.id, adminNote: noteDrafts[r.id] })}
                            >
                              Reject
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-400">Processed</span>
                      )}
                    </Td>
                  )}
                </Tr>
              ))}
            </TBody>
          </Table>
        </div>
      )}
    </Card>
  );
}
