'use client';

import {
  useUserStats,
  useUserPaymentInfo,
  useUserWithdrawals,
  useUserBids,
  useUserTransactions,
  useUserWinnings,
} from '@/hooks/useStudents';
import { LoadingState, EmptyState } from '@/components/ui/States';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { StatusBadge } from '@/components/ui/Badge';

export default function UserExpandedDetails({ studentId }: { studentId: number }) {
  const stats = useUserStats(studentId);
  const paymentInfo = useUserPaymentInfo(studentId);
  const withdrawals = useUserWithdrawals(studentId);
  const bids = useUserBids(studentId);
  const transactions = useUserTransactions(studentId);
  const winnings = useUserWinnings(studentId);

  return (
    <div className="p-4 bg-slate-50/50 space-y-6">
      {/* Wallet Stats */}
      <div>
        <h4 className="text-xs font-semibold uppercase text-slate-500 mb-2">Wallet Stats</h4>
        {stats.isLoading ? (
          <LoadingState />
        ) : stats.data ? (
          <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
            <div><p className="text-xs text-slate-400">Total Add Amount</p><p className="font-semibold text-emerald-600">{stats.data.total_added}</p></div>
            <div><p className="text-xs text-slate-400">Total Withdrawal</p><p className="font-semibold text-red-600">{stats.data.total_withdrawn}</p></div>
            <div><p className="text-xs text-slate-400">Overall In</p><p className="font-semibold text-emerald-600">{stats.data.overall_in}</p></div>
            <div><p className="text-xs text-slate-400">Overall Out</p><p className="font-semibold text-red-600">{stats.data.overall_out}</p></div>
          </div>
        ) : (
          <p className="text-sm text-slate-500">No stats available</p>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Payment Information */}
        <div>
          <h4 className="text-xs font-semibold uppercase text-slate-500 mb-2">Payment Information</h4>
          {paymentInfo.isLoading ? (
            <LoadingState />
          ) : paymentInfo.data?.length ? (
            <div className="border border-slate-200 rounded-lg overflow-hidden">
              <Table>
                <THead><Tr><Th>Method</Th><Th>Account/UPI</Th></Tr></THead>
                <TBody>
                  {paymentInfo.data.map(info => (
                    <Tr key={info.id}>
                      <Td className="py-2">{info.payment_method}</Td>
                      <Td className="py-2">{info.account_number || info.upi_id || '—'}</Td>
                    </Tr>
                  ))}
                </TBody>
              </Table>
            </div>
          ) : (
            <p className="text-sm text-slate-500">No payment methods</p>
          )}
        </div>

        {/* Withdrawal History */}
        <div>
          <h4 className="text-xs font-semibold uppercase text-slate-500 mb-2">Withdrawal History (Last 5)</h4>
          {withdrawals.isLoading ? (
            <LoadingState />
          ) : withdrawals.data?.length ? (
            <div className="border border-slate-200 rounded-lg overflow-hidden">
              <Table>
                <THead><Tr><Th>Date</Th><Th>Amount</Th><Th>Status</Th></Tr></THead>
                <TBody>
                  {withdrawals.data.slice(0, 5).map(w => (
                    <Tr key={w.id}>
                      <Td className="py-2">{new Date(w.created_at).toLocaleDateString()}</Td>
                      <Td className="py-2">{w.requested_amount}</Td>
                      <Td className="py-2"><StatusBadge status={w.status} /></Td>
                    </Tr>
                  ))}
                </TBody>
              </Table>
            </div>
          ) : (
            <p className="text-sm text-slate-500">No withdrawals</p>
          )}
        </div>

        {/* Bid History */}
        <div>
          <h4 className="text-xs font-semibold uppercase text-slate-500 mb-2">Bid History (Last 5)</h4>
          {bids.isLoading ? (
            <LoadingState />
          ) : bids.data?.length ? (
            <div className="border border-slate-200 rounded-lg overflow-hidden">
              <Table>
                <THead><Tr><Th>Game</Th><Th>Selection</Th><Th>Points</Th></Tr></THead>
                <TBody>
                  {bids.data.slice(0, 5).map(b => (
                    <Tr key={b.id}>
                      <Td className="py-2">{b.game_name}</Td>
                      <Td className="py-2">{b.selection}</Td>
                      <Td className="py-2">{b.points}</Td>
                    </Tr>
                  ))}
                </TBody>
              </Table>
            </div>
          ) : (
            <p className="text-sm text-slate-500">No bids</p>
          )}
        </div>

        {/* Wallet Transaction History */}
        <div>
          <h4 className="text-xs font-semibold uppercase text-slate-500 mb-2">Wallet Transactions (Last 5)</h4>
          {transactions.isLoading ? (
            <LoadingState />
          ) : transactions.data?.length ? (
            <div className="border border-slate-200 rounded-lg overflow-hidden">
              <Table>
                <THead><Tr><Th>Date</Th><Th>Type</Th><Th>Amount</Th></Tr></THead>
                <TBody>
                  {transactions.data.slice(0, 5).map(t => (
                    <Tr key={t.id}>
                      <Td className="py-2">{new Date(t.created_at).toLocaleDateString()}</Td>
                      <Td className="py-2">{t.type}</Td>
                      <Td className={`py-2 ${t.amount >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{t.amount}</Td>
                    </Tr>
                  ))}
                </TBody>
              </Table>
            </div>
          ) : (
            <p className="text-sm text-slate-500">No transactions</p>
          )}
        </div>

        {/* Winning History */}
        <div>
          <h4 className="text-xs font-semibold uppercase text-slate-500 mb-2">Winning History (Last 5)</h4>
          {winnings.isLoading ? (
            <LoadingState />
          ) : winnings.data?.length ? (
            <div className="border border-slate-200 rounded-lg overflow-hidden">
              <Table>
                <THead><Tr><Th>Date</Th><Th>Game</Th><Th>Won</Th></Tr></THead>
                <TBody>
                  {winnings.data.slice(0, 5).map(w => (
                    <Tr key={w.id}>
                      <Td className="py-2">{new Date(w.date).toLocaleDateString()}</Td>
                      <Td className="py-2">{w.game_name}</Td>
                      <Td className="py-2 text-emerald-600 font-bold">{w.winning_amount}</Td>
                    </Tr>
                  ))}
                </TBody>
              </Table>
            </div>
          ) : (
            <p className="text-sm text-slate-500">No winnings</p>
          )}
        </div>
      </div>
    </div>
  );
}
