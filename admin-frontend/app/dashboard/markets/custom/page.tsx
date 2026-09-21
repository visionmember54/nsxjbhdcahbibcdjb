import PageHeader from '@/components/layout/PageHeader';
import MarketsListView from '@/components/markets/MarketsListView';

export default function CustomMarketsPage() {
  return (
    <div>
      <PageHeader icon="market" title="Custom Markets" description="Markets in admin-defined categories beyond Matka/Starline/Gali-Disawar." />
      <MarketsListView category="CUSTOM" title="Custom Markets" />
    </div>
  );
}
