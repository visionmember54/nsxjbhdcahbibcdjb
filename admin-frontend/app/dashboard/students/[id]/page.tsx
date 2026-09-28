'use client';

import TempPassword from '@/components/ui/TempPassword';
import { useToast } from '@/components/ui/Feedback';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import PageHeader from '@/components/layout/PageHeader';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { StatusBadge } from '@/components/ui/Badge';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import {
  useStudent,
  useUserStats,
  useUserPaymentInfo,
  useUserWithdrawals,
  useUserBids,
  useUserTransactions,
  useUserWinnings,
  useResetPassword
} from '@/hooks/useStudents';
import Button from '@/components/ui/Button';
import { useState } from 'react';

export default function StudentDetailPage() {
  const params = useParams<{ id: string }>();
  const studentId = Number(params.id);
  const toast = useToast();
  const student = useStudent(studentId);
  const stats = useUserStats(studentId);
  const paymentInfo = useUserPaymentInfo(studentId);
  const withdrawals = useUserWithdrawals(studentId);
  const bids = useUserBids(studentId);
  const transactions = useUserTransactions(studentId);
  const winnings = useUserWinnings(studentId);
  const resetPassword = useResetPassword();

  const [tempPassword, setTempPassword] = useState<string | null>(null);

  if (student.isLoading) return <LoadingState />;
  if (student.isError) return <ErrorState message={(student.error as Error).message} />;
  if (!student.data) return <EmptyState title="User not found" />;
  const user = student.data;

  const handleResetPassword = () => {
    resetPassword.mutate(studentId, {
      onSuccess: (res) => setTempPassword(res.temporary_password),
    });
  };

  return <div>
    <PageHeader icon="users" title={user.name} description="Comprehensive user details view." action={<Link href={`/dashboard/wallet-activity/credits?studentId=${user.id}`} className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-gradient-to-b from-brand-500 to-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-glow transition-all hover:from-brand-400 hover:to-brand-500 active:scale-[0.98]">Manage Credits</Link>} />

    <Card className="mb-6">
      <CardHeader><CardTitle>User Details</CardTitle></CardHeader>
      <CardBody>
        <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4 lg:grid-cols-5">
          <div><p className="text-xs text-slate-500">Name</p><p className="font-semibold">{user.name}</p></div>
          <div><p className="text-xs text-slate-500">Phone</p><p>{user.phone}</p></div>
          <div><p className="text-xs text-slate-500">Email</p><p>{user.email || '—'}</p></div>
          <div><p className="text-xs text-slate-500">Status</p><StatusBadge status={user.status} /></div>
          <div><p className="text-xs text-slate-500">ID Creation Date</p><p>{new Date(user.created_at).toLocaleDateString()}</p></div>
          <div><p className="text-xs text-slate-500">Last Seen</p><p>{user.last_seen ? new Date(user.last_seen).toLocaleString() : 'Never'}</p></div>
          <div>
            <p className="text-xs text-slate-500">Password</p>
            <Button variant="secondary" size="sm" onClick={handleResetPassword} disabled={resetPassword.isPending}>
              {resetPassword.isPending ? 'Resetting...' : 'Reset Password'}
            </Button>
            {tempPassword && <div className="mt-2"><TempPassword password={tempPassword} /></div>}
          </div>
        </div>
      </CardBody>
    </Card>

    <Card className="mb-6">
      <CardHeader><CardTitle>Wallet Stats</CardTitle></CardHeader>
      <CardBody>
        {stats.isLoading ? <LoadingState /> : stats.data ? (
          <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-5">
            <div><p className="text-xs text-slate-500">Current Balance</p><p className="font-bold text-lg">{user.balance.toLocaleString()}</p></div>
            <div><p className="text-xs text-slate-500">Total Add Amount</p><p className="font-semibold text-emerald-600">{stats.data.total_added}</p></div>
            <div><p className="text-xs text-slate-500">Total Withdrawal Amount</p><p className="font-semibold text-red-600">{stats.data.total_withdrawn}</p></div>
            <div><p className="text-xs text-slate-500">Overall In (Credits)</p><p className="font-semibold text-emerald-600">{stats.data.overall_in}</p></div>
            <div><p className="text-xs text-slate-500">Overall Out (Credits)</p><p className="font-semibold text-red-600">{stats.data.overall_out}</p></div>
          </div>
        ) : <EmptyState title="No stats available" />}
      </CardBody>
    </Card>

    <Card className="mb-6">
      <CardHeader><CardTitle>Payment Information</CardTitle></CardHeader>
      <CardBody>
        {paymentInfo.isLoading ? <LoadingState /> : paymentInfo.data?.length ? (
          <Table>
            <THead><Tr><Th>Method</Th><Th>Account Name</Th><Th>Account / UPI</Th><Th>IFSC</Th></Tr></THead>
            <TBody>
              {paymentInfo.data.map(info => (
                <Tr key={info.id}>
                  <Td>{info.payment_method}</Td>
                  <Td>{info.account_name || '—'}</Td>
                  <Td>{info.account_number || info.upi_id || '—'}</Td>
                  <Td>{info.ifsc_code || '—'}</Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        ) : <EmptyState title="No payment information added" />}
      </CardBody>
    </Card>

    <Card className="mb-6">
      <CardHeader><CardTitle>Withdrawal History</CardTitle></CardHeader>
      <CardBody>
        {withdrawals.isLoading ? <LoadingState /> : withdrawals.data?.length ? (
          <Table>
            <THead><Tr><Th>Date</Th><Th>Amount</Th><Th>Status</Th></Tr></THead>
            <TBody>
              {withdrawals.data.map(w => (
                <Tr key={w.id}>
                  <Td>{new Date(w.created_at).toLocaleString()}</Td>
                  <Td>{w.requested_amount}</Td>
                  <Td><StatusBadge status={w.status} /></Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        ) : <EmptyState title="No withdrawal history" />}
      </CardBody>
    </Card>

    <Card className="mb-6">
      <CardHeader><CardTitle>Bid History (Front Games Only)</CardTitle></CardHeader>
      <CardBody>
        {bids.isLoading ? <LoadingState /> : bids.data?.length ? (
          <Table>
            <THead><Tr><Th>Date</Th><Th>Game</Th><Th>Type</Th><Th>Session</Th><Th>Selection</Th><Th>Points</Th><Th>Status</Th></Tr></THead>
            <TBody>
              {bids.data.map(b => (
                <Tr key={b.id}>
                  <Td>{new Date(b.created_at).toLocaleString()}</Td>
                  <Td>{b.game_name}</Td>
                  <Td>{b.game_type}</Td>
                  <Td>{b.session || '—'}</Td>
                  <Td>{b.selection}</Td>
                  <Td>{b.points}</Td>
                  <Td><StatusBadge status={b.status} /></Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        ) : <EmptyState title="No bid history" />}
      </CardBody>
    </Card>

    <Card className="mb-6">
      <CardHeader><CardTitle>Wallet Transaction History</CardTitle></CardHeader>
      <CardBody>
        {transactions.isLoading ? <LoadingState /> : transactions.data?.length ? (
          <Table>
            <THead><Tr><Th>Date</Th><Th>Type</Th><Th>Amount</Th><Th>Balance After</Th><Th>Note</Th></Tr></THead>
            <TBody>
              {transactions.data.map(t => (
                <Tr key={t.id}>
                  <Td>{new Date(t.created_at).toLocaleString()}</Td>
                  <Td>{t.type}</Td>
                  <Td className={t.amount >= 0 ? 'text-emerald-600' : 'text-red-600'}>{t.amount}</Td>
                  <Td>{t.balance_after}</Td>
                  <Td>{t.note || '—'}</Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        ) : <EmptyState title="No transactions" />}
      </CardBody>
    </Card>

    <Card className="mb-6">
      <CardHeader><CardTitle>Winning History</CardTitle></CardHeader>
      <CardBody>
        {winnings.isLoading ? <LoadingState /> : winnings.data?.length ? (
          <Table>
            <THead><Tr><Th>Date</Th><Th>Game</Th><Th>Winning Amount</Th><Th>Action</Th></Tr></THead>
            <TBody>
              {winnings.data.map(w => (
                <Tr key={w.id}>
                  <Td>{new Date(w.date).toLocaleString()}</Td>
                  <Td>{w.game_name}</Td>
                  <Td className="text-emerald-600 font-bold">{w.winning_amount}</Td>
                  <Td><Button variant="secondary" size="sm" onClick={() => toast(`Won ${w.winning_amount} on ${w.game_name} at ${new Date(w.date).toLocaleString()}`)}>View Details</Button></Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        ) : <EmptyState title="No winning history" />}
      </CardBody>
    </Card>
  </div>;
}
