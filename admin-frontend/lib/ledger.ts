const LEDGER_TYPE_LABELS: Record<string, string> = {
  stake: 'Bet',
};

export function ledgerTypeLabel(type: string): string {
  return LEDGER_TYPE_LABELS[type] ?? type.charAt(0).toUpperCase() + type.slice(1);
}
