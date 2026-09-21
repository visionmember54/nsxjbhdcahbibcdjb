'use client';

import { useEffect, useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { Table, TBody, Td, Th, THead, Tr } from '@/components/ui/Table';
import { LoadingState, ErrorState } from '@/components/ui/States';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import { FormField, Input } from '@/components/ui/Field';
import { useRoles, usePermissionCatalog, useCreateRole, useSetRolePermissions } from '@/hooks/useRoles';
import { Role } from '@/lib/api/types';

export default function RolesPage() {
  const { data: roles, isLoading, isError, error } = useRoles();
  const { data: permissions } = usePermissionCatalog();
  const createRole = useCreateRole();
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<Record<number, Set<string>>>({});

  useEffect(() => {
    if (!roles) return;
    setSelected((prev) => {
      const next = { ...prev };
      for (const role of roles) {
        if (!next[role.id]) next[role.id] = new Set(role.permissions);
      }
      return next;
    });
  }, [roles]);

  const setRolePermissions = useSetRolePermissions();

  function toggle(roleId: number, code: string) {
    setSelected((prev) => {
      const set = new Set(prev[roleId] ?? []);
      if (set.has(code)) set.delete(code);
      else set.add(code);
      return { ...prev, [roleId]: set };
    });
  }

  function isDirty(role: Role) {
    const current = selected[role.id];
    if (!current) return false;
    if (current.size !== role.permissions.length) return true;
    return role.permissions.some((c) => !current.has(c));
  }

  return (
    <div>
      <PageHeader
        icon="cog"
        title="Roles & Permissions"
        description="Every admin action is gated by a permission; a role is just a named set of them."
        action={<Button onClick={() => setOpen(true)}>+ New role</Button>}
      />

      {isLoading && <LoadingState />}
      {isError && <ErrorState message={(error as Error).message} />}

      {roles && permissions && (
        <Card>
          <Table>
            <THead>
              <Tr>
                <Th>Permission</Th>
                {roles.map((r) => (
                  <Th key={r.id} className="text-center">
                    {r.name}
                  </Th>
                ))}
              </Tr>
            </THead>
            <TBody>
              {permissions.map((p) => (
                <Tr key={p.id}>
                  <Td>
                    <div className="font-mono text-xs font-medium text-slate-900">{p.code}</div>
                    <div className="text-xs text-slate-500">{p.description}</div>
                  </Td>
                  {roles.map((r) => (
                    <Td key={r.id} className="text-center">
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                        checked={selected[r.id]?.has(p.code) ?? false}
                        onChange={() => toggle(r.id, p.code)}
                      />
                    </Td>
                  ))}
                </Tr>
              ))}
            </TBody>
          </Table>
          <CardBody className="flex flex-wrap gap-3 border-t border-slate-100">
            {roles.map((r) => (
              <Button
                key={r.id}
                size="sm"
                variant="secondary"
                disabled={!isDirty(r)}
                loading={setRolePermissions.isPending}
                onClick={() => setRolePermissions.mutate({ roleId: r.id, permissionCodes: Array.from(selected[r.id] ?? []) })}
              >
                Save {r.name}
              </Button>
            ))}
          </CardBody>
        </Card>
      )}

      <Modal open={open} onClose={() => setOpen(false)} title="New role">
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            const form = new FormData(e.currentTarget as HTMLFormElement);
            await createRole.mutateAsync({ slug: String(form.get('slug') || ''), name: String(form.get('name') || '') });
            setOpen(false);
          }}
        >
          <FormField label="Slug (used as the admin's `role` value)">
            <Input name="slug" required placeholder="e.g. auditor" pattern="[a-z0-9_]+" />
          </FormField>
          <FormField label="Display name">
            <Input name="name" required placeholder="e.g. Auditor" />
          </FormField>
          {createRole.isError && <p className="mb-2 text-xs text-red-600">{(createRole.error as Error).message}</p>}
          <Button type="submit" loading={createRole.isPending} className="w-full">
            Create role
          </Button>
        </form>
      </Modal>
    </div>
  );
}
