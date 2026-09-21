import PageHeader from '@/components/layout/PageHeader';
import MarketsListView from '@/components/markets/MarketsListView';

export default function GaliDisawarMarketsPage() {
  return (
    <div>
      <PageHeader icon="market" title="Gali–Disawar" description="Flat single/close/jodi markets." />
      <MarketsListView category="GALI_DISAWAR" title="Gali–Disawar Markets" />
    </div>
  );
}
