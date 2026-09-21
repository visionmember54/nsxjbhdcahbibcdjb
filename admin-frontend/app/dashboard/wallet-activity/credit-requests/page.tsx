'use client';

import { isHttpUrl } from '@/lib/security';
import { useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import { useCreditRequests, useApproveCreditRequest, useRejectCreditRequest } from '@/hooks/useCreditRequests';
import { usePermissions } from '@/hooks/usePermissions';
import type { CreditRequest } from '@/lib/api/types';

const STATUS_TONE: Record<CreditRequest['status'], 'amber' | 'green' | 'red'> = {
  Pending: 'amber',
  Approved: 'green',
  Rejected: 'red',
};

export default function CreditRequestsPage() {
  const { data, isLoading, isError, error } = useCreditRequests({ limit: 100 });
  const approve = useApproveCreditRequest();
  const reject = useRejectCreditRequest();
  const { has } = usePermissions();
  const canManage = has('credits.manage');

  const [filter, setFilter] = useState<'' | CreditRequest['status']>('Pending');
  const [noteDrafts, setNoteDrafts] = useState<Record<number, string>>({});

  const requests = (data?.items ?? []).filter((r) => !filter || r.status === filter);
  const pendingCount = (data?.items ?? []).filter((r) => r.status === 'Pending').length;

  return (
    <div>
      <PageHeader
        icon="coin"
        title="Credit Requests"
        description="Users asking for more virtual Learning Credits — approve to grant them for free, or reject."
        action={pendingCount > 0 ? <Badge tone="amber">{pendingCount} pending</Badge> : undefined}
      />

      <Card>
        <div className="flex gap-1 border-b border-slate-100 px-4 py-3">
          {(['', 'Pending', 'Approved', 'Rejected'] as const).map((s) => (
            <button
              key={s || 'all'}
              onClick={() => setFilter(s)}
              className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-colors ${filter === s ? 'bg-brand-600 text-white' : 'text-slate-500 hover:bg-slate-100'
                }`}
            >
              {s || 'All'}
            </button>
          ))}
        </div>

        {isLoading && <LoadingState />}
        {isError && <ErrorState message={(error as Error).message} />}
        {!isLoading && !isError && requests.length === 0 && (
          <EmptyState title="No credit requests" hint={filter ? `No ${filter.toLowerCase()} requests right now.` : 'Requests will show up here as users ask for more credits.'} />
        )}

        {!isLoading && !isError && requests.length > 0 && (
          <Table>
            <THead>
              <Tr>
                <Th>User</Th>
                <Th>Type</Th>
                <Th>Amount</Th>
                <Th>Details</Th>
                <Th>Status</Th>
                <Th>Requested</Th>
                {canManage && <Th></Th>}
              </Tr>
            </THead>
            <TBody>
              {requests.map((r) => (
                <Tr key={r.id}>
                  <Td className="font-medium text-slate-900">
                    {r.userName}
                    <span className="ml-1.5 text-xs font-normal text-slate-400">{r.userPhone}</span>
                  </Td>
                  <Td>
                    <Badge tone={r.requestType.toLowerCase() === 'withdrawal' ? 'amber' : 'green'}>
                      {r.requestType}
                    </Badge>
                  </Td>
                  <Td className="font-semibold text-brand-700">
                    {r.requestType.toLowerCase() === 'withdrawal' ? '-' : '+'}{r.requestedAmount.toLocaleString()}
                  </Td>
                  <Td className="max-w-[200px] text-xs text-slate-600 space-y-1">
                    {r.utrNumber && <div><span className="font-semibold">UTR:</span> {r.utrNumber}</div>}
                    {r.paymentDetails && <div><span className="font-semibold">To:</span> {r.paymentDetails}</div>}
                    {isHttpUrl(r.screenshotUrl) && (
                      <a href={r.screenshotUrl} target="_blank" rel="noreferrer" className="text-brand-600 hover:underline">
                        View Screenshot
                      </a>
                    )}
                    {r.reason && <div className="truncate" title={r.reason}>{r.reason}</div>}
                    {!r.utrNumber && !r.paymentDetails && !isHttpUrl(r.screenshotUrl) && !r.reason && '—'}
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
                      {r.status === 'Pending' && (
                        <div className="flex items-center gap-2">
                          <input
                            className="w-32 rounded-md border border-slate-200 px-2 py-1 text-xs placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
                            placeholder="Note (optional)"
                            value={noteDrafts[r.id] ?? ''}
                            onChange={(e) => setNoteDrafts((prev) => ({ ...prev, [r.id]: e.target.value }))}
                          />
                          <Button
                            size="sm"
                            loading={approve.isPending}
                            onClick={() => approve.mutate({ id: r.id, adminNote: noteDrafts[r.id] })}
                          >
                            Approve
                          </Button>
                          <Button
                            size="sm"
                            variant="danger"
                            loading={reject.isPending}
                            onClick={() => reject.mutate({ id: r.id, adminNote: noteDrafts[r.id] })}
                          >
                            Reject
                          </Button>
                        </div>
                      )}
                    </Td>
                  )}
                </Tr>
              ))}
            </TBody>
          </Table>
        )}

        {(approve.isError || reject.isError) && (
          <p className="border-t border-slate-100 px-4 py-2 text-xs text-red-600">
            {((approve.error || reject.error) as Error).message}
          </p>
        )}
      </Card>
    </div>
  );
}
