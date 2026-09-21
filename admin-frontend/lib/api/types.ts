// Hand-curated ergonomic types mirroring the backend's Pydantic schemas
// exactly (field names, casing). lib/api/schema.d.ts is generated from the
// live OpenAPI spec via `npm run gen:types` and can be cross-checked against
// these; these are what the hooks actually consume.

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface AdminUser {
  id: number;
  name: string;
  email: string;
  role: string;
  status: 'active' | 'disabled';
  permissions: string[];
}

export interface Permission {
  id: number;
  code: string;
  description: string;
}

export interface Role {
  id: number;
  slug: string;
  name: string;
  permissions: string[];
}

export interface Student {
  id: number;
  name: string;
  phone: string;
  email: string;
  status: 'active' | 'disabled';
  balance: number;
  last_seen: string | null;
  created_at: string;
}

export interface UserStats {
  total_added: number;
  total_withdrawn: number;
  overall_in: number;
  overall_out: number;
}

export interface UserPaymentInfo {
  id: number;
  payment_method: string;
  account_name: string | null;
  account_number: string | null;
  ifsc_code: string | null;
  upi_id: string | null;
}

export interface UserWithdrawal {
  id: number;
  requested_amount: number;
  status: string;
  created_at: string;
}

export interface UserBid {
  id: number;
  game_name: string;
  game_type: string;
  session: string | null;
  selection: string;
  points: number;
  created_at: string;
  status: string;
}

export interface UserTransaction {
  id: number;
  type: string;
  amount: number;
  balance_after: number;
  note: string | null;
  created_at: string;
}

export interface UserWinning {
  id: number;
  date: string;
  game_name: string;
  winning_amount: number;
}

export interface MarketCategory {
  id: number;
  slug: string;
  name: string;
  display_order: number;
}

export interface GameType {
  id: number;
  code: string;
  name: string;
  description: string;
  digit_length: number;
  classification_rule: 'NONE' | 'PANNA_SINGLE' | 'PANNA_DOUBLE' | 'PANNA_TRIPLE' | 'SANGAM_HALF' | 'SANGAM_FULL';
  is_active: boolean;
  display_order: number;
}

export type MarketStatus = 'UPCOMING' | 'OPEN' | 'CLOSED' | 'RESULT_PENDING' | 'RESULT_PUBLISHED' | 'SUSPENDED';

export interface Market {
  id: number;
  category_id: number;
  category: string;
  name: string;
  slug: string;
  description: string;
  status: MarketStatus;
  timezone: string;
  opening_time: string | null;
  closing_time: string | null;
  cutoff_time: string | null;
  result_time: string | null;
  display_order: number;
}

export interface StarlineSlot {
  id: number;
  market_id: number;
  slot_name: string;
  start_time: string;
  cutoff_time: string;
  enabled: boolean;
  display_order: number;
}

export interface GameTypeConfig {
  id: number;
  market_id: number;
  slot_id: number | null;
  game_type_id: number;
  game_type_code: string;
  stage: 'OPEN' | 'CLOSE' | 'BOTH' | null;
  enabled: boolean;
  min_credits: number;
  max_credits: number;
  bulk_enabled: boolean;
  max_bulk_selections: number;
  same_amount_allowed: boolean;
  individual_amount_allowed: boolean;
  duplicate_selection_allowed: boolean;
}

export interface Rate {
  id: number;
  market_id: number;
  slot_id: number | null;
  game_type_id: number;
  game_type_code: string;
  rate: number;
  effective_from: string;
  status: 'Active' | 'Inactive';
}

export interface CreditLedgerEntry {
  id: number;
  student_id: number;
  type: 'grant' | 'adjustment' | 'reset' | 'stake' | 'payout';
  amount: number;
  balanceAfter: number;
  referenceType: string | null;
  referenceId: string | null;
  note: string | null;
  visibleToUser: boolean;
  createdAt: string;
}

export interface SimulationEntry {
  id: number;
  batchId: number;
  userId: number;
  marketId: number;
  slotId: number | null;
  gameType: string;
  stage: string | null;
  selection: string;
  gameVariant: 'OPEN_PANNA_CLOSE_ANK' | 'OPEN_ANK_CLOSE_PANNA' | null;
  simulatedCredits: number;
  simulatedRate: number;
  simulatedReturn: number;
  status: 'Pending' | 'Won' | 'Lost' | 'Cancelled';
  createdAt: string;
  resolvedAt: string | null;
  originalStatus: string | null;
  overrideStatus: string | null;
  overrideReason: string | null;
  overriddenByAdminId: number | null;
  overriddenAt: string | null;
}

export interface SimulationBatchResult {
  batchId: number;
  entries: SimulationEntry[];
  totalCredits: number;
  remainingBalance: number;
}

export interface MarketResult {
  id: number;
  marketId: number;
  slotId: number | null;
  date: string;
  openPanna: string | null;
  openAnk: string | null;
  closePanna: string | null;
  closeAnk: string | null;
  jodi: string | null;
  singleResult: string | null;
  status: 'Draft' | 'Published' | 'Corrected';
  publishedAt: string | null;
  correctedFromId: number | null;
  correctionReason: string | null;
}

export interface SupportQueryMessage {
  id: number;
  sender: 'user' | 'admin';
  text: string;
  time: string;
}

export interface SupportQuery {
  id: number;
  user: string;
  subject: string;
  status: 'Open' | 'Pending';
  priority: 'Low' | 'Normal' | 'High';
  updatedAt: string;
  messages: SupportQueryMessage[];
}

export interface CreditRequest {
  id: number;
  userId: number;
  userName: string;
  userPhone: string;
  requestedAmount: number;
  requestType: string;
  utrNumber: string | null;
  screenshotUrl: string | null;
  paymentDetails: string | null;
  reason: string | null;
  status: 'Pending' | 'Approved' | 'Rejected';
  adminNote: string | null;
  reviewedByAdminId: number | null;
  reviewedAt: string | null;
  createdAt: string;
}

export interface ResultPreviewWinner {
  entryId: number;
  userId: number;
  userName: string;
  userPhone: string;
  gameType: string;
  stage: string | null;
  selection: string;
  gameVariant: string | null;
  credits: number;
  simulatedRate: number;
  potentialPayout: number;
}

export interface ResultPreview {
  openPanna: string | null;
  openAnk: string | null;
  closePanna: string | null;
  closeAnk: string | null;
  jodi: string | null;
  totalPendingEntries: number;
  resolvableEntries: number;
  unresolvedEntries: number;
  winnersCount: number;
  losersCount: number;
  totalStakeAtRisk: number;
  totalPotentialPayout: number;
  winners: ResultPreviewWinner[];
}

export interface SiteSetting {
  key: string;
  value: string;
}

export interface HomepageBanner {
  id: number;
  image_url: string;
  title: string;
  link: string;
  display_order: number;
  enabled: boolean;
}

export interface ScrollingMessage {
  id: number;
  text: string;
  display_order: number;
  enabled: boolean;
}

export interface EducationalContent {
  id: number;
  game_type_id: number | null;
  title: string;
  description: string;
  how_it_works: string;
  example: string;
  probability_explanation: string;
  rules: string;
}

export interface FAQ {
  id: number;
  question: string;
  answer: string;
  display_order: number;
  enabled: boolean;
}

export interface AuditLogEntry {
  id: number;
  actor: string;
  action: string;
  details: string;
  subjectUserId: number | null;
  createdAt: string;
}

export interface MarketStatistic {
  marketId: number;
  market: string;
  sales: number;
  winners: number;
  payout: number;
  profit: number;
}

export interface DailyMarketPerformance {
  marketId: number;
  market: string;
  simulations: number;
  staked: number;
  payout: number;
  net: number;
}

export interface GameStatistic {
  gameType: string;
  sales: number;
  winners: number;
  payout: number;
  profit: number;
}

export interface NumberFrequency {
  selection: string;
  count: number;
}

export interface DashboardData {
  stats: {
    totalUsers: number;
    activeUsers: number;
    openMarkets: number;
    pendingResults: number;
    totalSimulations: number;
    totalCreditsStaked: number;
    totalCreditsPaidOut: number;
    totalNetCredits: number;
    totalWon: number;
    totalLost: number;
    totalPending: number;
    activeStarlineSlots: number;
  };
  today: {
    date: string;
    simulations: number;
    staked: number;
    payout: number;
    net: number;
    won: number;
    pending: number;
    newUsers: number;
    publishedResults: number;
  };
  todayMarketPerformance: DailyMarketPerformance[];
  marketStatistics: MarketStatistic[];
  popularMarket: { name: string; count: number } | null;
  popularGame: { code: string; count: number } | null;
  upcomingMarkets: { id: number; name: string; openingTime: string | null; cutoffTime: string | null }[];
  recentAdminActions: AuditLogEntry[];
}
