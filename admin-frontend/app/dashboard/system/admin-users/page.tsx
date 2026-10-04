'use client';

import { useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import { StatusBadge } from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import { FormField, Input, Select } from '@/components/ui/Field';
import Pagination from '@/components/ui/Pagination';
import { useAdmins, useCreateAdmin, useUpdateAdmin } from '@/hooks/useAdmins';
import { useCurrentAdmin } from '@/hooks/useAuth';
import { usePermissions } from '@/hooks/usePermissions';
import { useRoles } from '@/hooks/useRoles';

export default function AdminUsersPage() {
  const [offset, setOffset] = useState(0);
  const [open, setOpen] = useState(false);
  const [editingPhoneId, setEditingPhoneId] = useState<number | null>(null);
  const limit = 20;
  const { data, isLoading, isError, error } = useAdmins({ limit, offset });
  const { data: me } = useCurrentAdmin();
  const { data: roles } = useRoles();
  const createAdmin = useCreateAdmin();
  const updateAdmin = useUpdateAdmin();
  const { has } = usePermissions();

  const canManageAdmins = has('admins.manage');
  const editingPhoneAdmin = data?.items.find((a) => a.id === editingPhoneId);

  return (
    <div>
      <PageHeader
        icon="cog"
        title="Admin Users"
        description="Admin-panel operator accounts."
        action={canManageAdmins ? <Button onClick={() => setOpen(true)}>+ New admin</Button> : undefined}
      />
      <Card>
        {isLoading && <LoadingState />}
        {isError && <ErrorState message={(error as Error).message} />}
        {data && data.items.length === 0 && <EmptyState title="No admins yet" />}

        {data && data.items.length > 0 && (
          <Table>
            <THead>
              <Tr>
                <Th>Name</Th>
                <Th>Email</Th>
                <Th>Role</Th>
                <Th>Phone</Th>
                <Th>Status</Th>
                <Th></Th>
              </Tr>
            </THead>
            <TBody>
              {data.items.map((a) => (
                <Tr key={a.id}>
                  <Td className="font-medium text-slate-900">{a.name}</Td>
                  <Td>{a.email}</Td>
                  <Td>{a.role}</Td>
                  <Td>
                    <span className={a.phone ? '' : 'text-slate-400'}>{a.phone || 'Not set'}</span>
                    {canManageAdmins && (
                      <button
                        className="ml-2 text-xs font-semibold text-brand-600 hover:underline"
                        onClick={() => setEditingPhoneId(a.id)}
                      >
                        Edit
                      </button>
                    )}
                  </Td>
                  <Td>
                    <StatusBadge status={a.status} />
                  </Td>
                  <Td>
                    {canManageAdmins && a.id !== me?.id && (
                      <button
                        className="text-xs font-semibold text-brand-600 hover:underline"
                        onClick={() => updateAdmin.mutate({ id: a.id, status: a.status === 'active' ? 'disabled' : 'active' })}
                      >
                        {a.status === 'active' ? 'Disable' : 'Enable'}
                      </button>
                    )}
                  </Td>
                </Tr>
              ))}
            </TBody>
          </Table>
        )}
        {data && <Pagination total={data.total} limit={limit} offset={offset} onOffsetChange={setOffset} />}
      </Card>

      <Modal open={open} onClose={() => setOpen(false)} title="New admin">
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            const form = new FormData(e.currentTarget as HTMLFormElement);
            await createAdmin.mutateAsync({
              name: String(form.get('name') || ''),
              email: String(form.get('email') || ''),
              password: String(form.get('password') || ''),
              role: String(form.get('role') || 'admin'),
              phone: String(form.get('phone') || '') || undefined,
            });
            setOpen(false);
          }}
        >
          <FormField label="Name">
            <Input name="name" required />
          </FormField>
          <FormField label="Email">
            <Input name="email" type="email" required />
          </FormField>
          <FormField label="Password">
            <Input name="password" type="password" required minLength={8} autoComplete="new-password" />
          </FormField>
          <FormField label="Role">
            <Select name="role" defaultValue="admin">
              {(roles ?? []).map((r) => (
                <option key={r.slug} value={r.slug}>
                  {r.name}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="Phone (receives OTP for payment-setting changes)">
            <Input name="phone" placeholder="e.g. +91 7000000000" />
          </FormField>
          {createAdmin.isError && <p className="mb-2 text-xs text-red-600">{(createAdmin.error as Error).message}</p>}
          <Button type="submit" loading={createAdmin.isPending} className="w-full">
            Create
          </Button>
        </form>
      </Modal>

      <Modal open={!!editingPhoneAdmin} onClose={() => setEditingPhoneId(null)} title={`Edit phone — ${editingPhoneAdmin?.name ?? ''}`}>
        {editingPhoneAdmin && (
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              const form = new FormData(e.currentTarget as HTMLFormElement);
              await updateAdmin.mutateAsync({ id: editingPhoneAdmin.id, phone: String(form.get('phone') || '') });
              setEditingPhoneId(null);
            }}
          >
            <FormField label="Phone (receives OTP for payment-setting changes)">
              <Input name="phone" defaultValue={editingPhoneAdmin.phone ?? ''} placeholder="e.g. +91 7000000000" />
            </FormField>
            {updateAdmin.isError && <p className="mb-2 text-xs text-red-600">{(updateAdmin.error as Error).message}</p>}
            <Button type="submit" loading={updateAdmin.isPending} className="w-full">
              Save
            </Button>
          </form>
        )}
      </Modal>
    </div>
  );
}
