import PageHeader from '@/components/layout/PageHeader';
import MarketsListView from '@/components/markets/MarketsListView';

export default function AllMarketsPage() {
  return (
    <div>
      <PageHeader icon="market" title="All Markets" description="Every market across every category." />
      <MarketsListView title="All Markets" />
    </div>
  );
}
