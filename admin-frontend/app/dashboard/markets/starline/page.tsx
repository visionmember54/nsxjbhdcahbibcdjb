import PageHeader from '@/components/layout/PageHeader';
import MarketsListView from '@/components/markets/MarketsListView';

export default function StarlineMarketsPage() {
  return (
    <div>
      <PageHeader icon="market" title="Starline" description="Slot-based markets — open a market to manage its daily time slots." />
      <MarketsListView category="STARLINE" title="Starline Markets" />
    </div>
  );
}
