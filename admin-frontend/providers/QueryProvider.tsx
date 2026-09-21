'use client';

import { MutationCache, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
import { FeedbackProvider, useToast } from '@/components/ui/Feedback';
import { ApiError } from '@/lib/api/client';

function Queries({ children }: { children: React.ReactNode }) {
  const toast = useToast();
  const [client] = useState(
    () =>
      new QueryClient({
        // Every mutation reports its outcome; opt out with `meta: { silent: true }`.
        mutationCache: new MutationCache({
          onSuccess: (_d, _v, _c, mutation) => {
            if (!mutation.meta?.silent) toast('Saved');
          },
          onError: (error, _v, _c, mutation) => {
            if (mutation.meta?.silent || (error instanceof ApiError && error.status === 401)) return;
            toast(error.message || 'Something went wrong', 'error');
          },
        }),
        defaultOptions: {
          queries: {
            staleTime: 15_000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      }),
  );

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

export default function QueryProvider({ children }: { children: React.ReactNode }) {
  return (
    <FeedbackProvider>
      <Queries>{children}</Queries>
    </FeedbackProvider>
  );
}
