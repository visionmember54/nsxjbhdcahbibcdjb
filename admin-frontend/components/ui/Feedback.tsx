'use client';

import { createContext, useCallback, useContext, useRef, useState } from 'react';
import Modal from './Modal';
import Button from './Button';

type ToastTone = 'success' | 'error';
type ToastItem = { id: number; tone: ToastTone; message: string };
type ConfirmState = { message: string; resolve: (ok: boolean) => void } | null;

const FeedbackContext = createContext<{
  toast: (message: string, tone?: ToastTone) => void;
  confirm: (message: string) => Promise<boolean>;
} | null>(null);

export function useToast() {
  const ctx = useContext(FeedbackContext);
  if (!ctx) throw new Error('useToast must be used inside FeedbackProvider');
  return ctx.toast;
}

/** Promise-based replacement for window.confirm: `if (await confirm('Delete?')) ...` */
export function useConfirm() {
  const ctx = useContext(FeedbackContext);
  if (!ctx) throw new Error('useConfirm must be used inside FeedbackProvider');
  return ctx.confirm;
}

export function FeedbackProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [pending, setPending] = useState<ConfirmState>(null);
  const nextId = useRef(0);

  const toast = useCallback((message: string, tone: ToastTone = 'success') => {
    const id = nextId.current++;
    setToasts((t) => [...t, { id, tone, message }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 5000);
  }, []);

  const confirm = useCallback(
    (message: string) => new Promise<boolean>((resolve) => setPending({ message, resolve })),
    [],
  );

  function answer(ok: boolean) {
    pending?.resolve(ok);
    setPending(null);
  }

  return (
    <FeedbackContext.Provider value={{ toast, confirm }}>
      {children}

      <div className="pointer-events-none fixed bottom-4 right-4 z-[60] flex w-80 max-w-[calc(100vw-2rem)] flex-col gap-2" aria-live="polite">
        {toasts.map((t) => (
          <div
            key={t.id}
            role={t.tone === 'error' ? 'alert' : 'status'}
            className={`pointer-events-auto rounded-lg px-4 py-3 text-sm font-medium shadow-lg ring-1 ${
              t.tone === 'error' ? 'bg-red-50 text-red-800 ring-red-200' : 'bg-emerald-50 text-emerald-800 ring-emerald-200'
            }`}
          >
            {t.message}
          </div>
        ))}
      </div>

      <Modal open={!!pending} onClose={() => answer(false)} title="Please confirm" maxWidth="max-w-sm">
        <p className="mb-5 text-sm text-slate-600">{pending?.message}</p>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={() => answer(false)}>Cancel</Button>
          <Button variant="danger" onClick={() => answer(true)}>Confirm</Button>
        </div>
      </Modal>
    </FeedbackContext.Provider>
  );
}
