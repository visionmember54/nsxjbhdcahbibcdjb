'use client';

import { useState } from 'react';
import Button from './Button';

/** Shows a server-generated temporary password once, with a copy button. */
export default function TempPassword({ password }: { password: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div role="status" className="rounded-lg bg-amber-50 p-3 text-xs text-amber-900 ring-1 ring-amber-200">
      <p className="mb-1.5 font-semibold">Temporary password — shown once. Share it securely with the user.</p>
      <div className="flex items-center gap-2">
        <code className="select-all rounded bg-white px-2 py-1 font-mono text-sm">{password}</code>
        <Button
          type="button"
          size="sm"
          variant="secondary"
          onClick={() => navigator.clipboard?.writeText(password).then(() => setCopied(true)).catch(() => {})}
        >
          {copied ? 'Copied' : 'Copy'}
        </Button>
      </div>
    </div>
  );
}
