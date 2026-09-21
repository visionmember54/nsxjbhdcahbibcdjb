'use client';

import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import { FormField, Input } from '@/components/ui/Field';
import TempPassword from '@/components/ui/TempPassword';
import { useCreateStudent } from '@/hooks/useStudents';

export default function CreateStudentModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const createStudent = useCreateStudent();
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [tempPassword, setTempPassword] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const created = await createStudent.mutateAsync({ name, phone, email });
    setName('');
    setPhone('');
    setEmail('');
    if (created.temporary_password) setTempPassword(created.temporary_password);
    else onClose();
  }

  function close() {
    setTempPassword(null);
    onClose();
  }

  if (tempPassword) {
    return (
      <Modal open={open} onClose={close} title="User created">
        <TempPassword password={tempPassword} />
        <div className="mt-4 flex justify-end">
          <Button onClick={close}>Done</Button>
        </div>
      </Modal>
    );
  }

  return (
    <Modal open={open} onClose={onClose} title="Create user">
      <form onSubmit={handleSubmit}>
        <FormField label="Name">
          <Input required value={name} onChange={(e) => setName(e.target.value)} />
        </FormField>
        <FormField label="Phone">
          <Input required value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="10-digit phone" />
        </FormField>
        <FormField label="Email (optional)">
          <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </FormField>
        <p className="mb-3 text-xs text-slate-400">A random temporary password is generated and shown once after creation; the user can change it after signing in.</p>
        {createStudent.isError && <p className="mb-3 text-xs text-red-600">{(createStudent.error as Error).message}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={createStudent.isPending}>
            Create user
          </Button>
        </div>
      </form>
    </Modal>
  );
}
