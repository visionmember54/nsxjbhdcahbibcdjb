'use client';

import { useMemo, useState } from 'react';
import { useMarkets } from '@/hooks/useMarkets';
import { useMarketCategories } from '@/hooks/useMarketCategories';
import { Card } from '@/components/ui/Card';
import { Table, TBody, Th, THead, Tr } from '@/components/ui/Table';
import Badge from '@/components/ui/Badge';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import Pagination from '@/components/ui/Pagination';
import Button from '@/components/ui/Button';
import CreateMarketModal from './CreateMarketModal';
import MarketRow from './MarketRow';
import type { Market } from '@/lib/api/types';

// Cycled by a category's position in the list, not hardcoded per slug, so a
// brand-new custom category still gets a distinct, deliberate color.
const CATEGORY_TONES: Array<'blue' | 'purple' | 'amber' | 'green'> = ['blue', 'purple', 'amber', 'green'];
const ACCENT_BAR: Record<string, string> = {
  blue: 'bg-blue-500',
  purple: 'bg-purple-500',
  amber: 'bg-amber-500',
  green: 'bg-emerald-500',
};

function GroupTable({ markets, showCategory }: { markets: Market[]; showCategory: boolean }) {
  return (
    <Table>
      <THead>
        <Tr>
          <Th>Order</Th>
          <Th>Name</Th>
          {showCategory && <Th>Category</Th>}
          <Th>Status</Th>
          <Th>Opening</Th>
          <Th>Closing</Th>
          <Th>Result</Th>
          <Th>Visible</Th>
          <Th></Th>
        </Tr>
      </THead>
      <TBody>
        {markets.map((market) => (
          <MarketRow key={market.id} market={market} showCategory={showCategory} />
        ))}
      </TBody>
    </Table>
  );
}

/** The "All Markets" view: every market across every category in one place,
 * grouped so each bazaar type reads as its own section instead of one long
 * undifferentiated list, with the display-order that drives the app's main
 * screen editable right in the row -- no need to open the market at all. */
function GroupedMarketsView({ onCreate }: { onCreate: () => void }) {
  const { data: categories, isLoading: categoriesLoading } = useMarketCategories();
  // One page covers every real-world market count comfortably; grouping by
  // category doesn't mix well with row-level pagination, so this view trades
  // paging for a single complete fetch instead.
  const { data, isLoading, isError, error } = useMarkets({ limit: 250 });

  const grouped = useMemo(() => {
    if (!data || !categories) return [];
    const bySlug = new Map<string, Market[]>();
    for (const market of data.items) {
      const list = bySlug.get(market.category) ?? [];
      list.push(market);
      bySlug.set(market.category, list);
    }
    return categories
      .map((cat) => ({
        category: cat,
        markets: (bySlug.get(cat.slug) ?? []).slice().sort((a, b) => a.display_order - b.display_order || a.id - b.id),
      }))
      .filter((group) => group.markets.length > 0);
  }, [data, categories]);

  const busy = isLoading || categoriesLoading;

  return (
    <Card>
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold text-slate-900">All Markets</h2>
          <p className="mt-0.5 text-xs text-slate-500">Grouped by category. Set the app's main-screen order right here.</p>
        </div>
        <Button size="sm" onClick={onCreate}>
          + New market
        </Button>
      </div>

      {busy && <LoadingState />}
      {isError && <ErrorState message={(error as Error).message} />}
      {!busy && grouped.length === 0 && <EmptyState title="No markets yet" hint="Create one to get started." />}

      {!busy &&
        grouped.map((group, i) => {
          const tone = CATEGORY_TONES[i % CATEGORY_TONES.length];
          return (
            <div key={group.category.id} className="border-b border-slate-100 last:border-b-0">
              <div className="flex items-center gap-2.5 bg-slate-50/60 px-5 py-2.5">
                <span className={`h-2.5 w-2.5 rounded-full ${ACCENT_BAR[tone]}`} aria-hidden="true" />
                <h3 className="text-xs font-bold uppercase tracking-wide text-slate-700">{group.category.name}</h3>
                <Badge tone={tone}>{group.markets.length}</Badge>
              </div>
              <GroupTable markets={group.markets} showCategory={false} />
            </div>
          );
        })}
    </Card>
  );
}

/** A single category's markets, paginated -- used by the Matka / Starline /
 * Gali-Disawar / Custom pages, which are each already scoped to one
 * category, so grouping would just repeat the page title as a lone group. */
function FlatMarketsView({ category, title, onCreate }: { category: string; title: string; onCreate: () => void }) {
  const [offset, setOffset] = useState(0);
  const limit = 20;
  const { data, isLoading, isError, error } = useMarkets({ category, limit, offset });

  return (
    <Card>
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
        <Button size="sm" onClick={onCreate}>
          + New market
        </Button>
      </div>

      {isLoading && <LoadingState />}
      {isError && <ErrorState message={(error as Error).message} />}
      {data && data.items.length === 0 && <EmptyState title="No markets yet" hint="Create one to get started." />}
      {data && data.items.length > 0 && <GroupTable markets={data.items} showCategory={false} />}

      {data && <Pagination total={data.total} limit={limit} offset={offset} onOffsetChange={setOffset} />}
    </Card>
  );
}

export default function MarketsListView({ category, title }: { category?: string; title: string }) {
  const [createOpen, setCreateOpen] = useState(false);

  return (
    <>
      {category ? (
        <FlatMarketsView category={category} title={title} onCreate={() => setCreateOpen(true)} />
      ) : (
        <GroupedMarketsView onCreate={() => setCreateOpen(true)} />
      )}
      <CreateMarketModal open={createOpen} onClose={() => setCreateOpen(false)} defaultCategorySlug={category} />
    </>
  );
}
