'use client';

import { useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { FormField, Select } from '@/components/ui/Field';
import Pagination from '@/components/ui/Pagination';
import SimulationsTable from '@/components/simulations/SimulationsTable';
import { useSimulations } from '@/hooks/useSimulations';
import { useStudents } from '@/hooks/useStudents';

export default function StudentHistoryPage() {
  const { data: studentsPage } = useStudents({ limit: 100 });
  const [studentId, setStudentId] = useState<number | ''>('');
  const [offset, setOffset] = useState(0);
  const limit = 20;

  const { data, isLoading, isError, error } = useSimulations({ studentId: studentId || undefined, limit, offset });

  return (
    <div>
      <PageHeader icon="play" title="User History" description="Every selection a specific user has submitted." />
      <Card>
        <div className="border-b border-slate-100 p-4">
          <FormField label="User">
            <Select
              value={studentId}
              onChange={(e) => {
                setStudentId(e.target.value ? Number(e.target.value) : '');
                setOffset(0);
              }}
              className="max-w-xs"
            >
              <option value="">All users</option>
              {studentsPage?.items.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </Select>
          </FormField>
        </div>
        <SimulationsTable
          entries={data?.items}
          isLoading={isLoading}
          isError={isError}
          errorMessage={(error as Error)?.message}
          showStudent={!studentId}
        />
        {data && <Pagination total={data.total} limit={limit} offset={offset} onOffsetChange={setOffset} />}
      </Card>
    </div>
  );
}
