import PageHeader from '@/components/layout/PageHeader';
import MarketsListView from '@/components/markets/MarketsListView';

export default function MatkaMarketsPage() {
  return (
    <div>
      <PageHeader icon="market" title="Main / Matka Markets" description="Open + Close session markets with Single/Jodi/Panna game types." />
      <MarketsListView category="MATKA" title="Matka Markets" />
    </div>
  );
}
