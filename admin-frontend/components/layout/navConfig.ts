import type { IconKey } from './icons';

export interface NavItem {
  label: string;
  href: string;
  permission?: string; // hidden when the admin lacks it (UI only; backend enforces)
}

export interface NavSection {
  title: string | null;
  icon: IconKey;
  items: NavItem[];
}

export const NAV_SECTIONS: NavSection[] = [
  { title: null, icon: 'home', items: [{ label: 'Dashboard', href: '/dashboard' }] },
  {
    title: 'Markets',
    icon: 'market',
    items: [
      { label: 'All Markets', href: '/dashboard/markets' },
      { label: 'Main / Matka Markets', href: '/dashboard/markets/matka' },
      { label: 'Starline', href: '/dashboard/markets/starline' },
      { label: 'Gali–Disawar', href: '/dashboard/markets/gali-disawar' },
      { label: 'Custom Markets', href: '/dashboard/markets/custom' },
    ],
  },
  {
    title: 'Configuration',
    icon: 'sliders',
    items: [
      { label: 'Single', href: '/dashboard/game-config/SINGLE' },
      { label: 'Jodi', href: '/dashboard/game-config/JODI' },
      { label: 'Single Panna', href: '/dashboard/game-config/SINGLE_PANNA' },
      { label: 'Double Panna', href: '/dashboard/game-config/DOUBLE_PANNA' },
      { label: 'Triple Panna', href: '/dashboard/game-config/TRIPLE_PANNA' },
      { label: 'Half Sangam', href: '/dashboard/game-config/HALF_SANGAM' },
      { label: 'Full Sangam', href: '/dashboard/game-config/FULL_SANGAM' },
      { label: 'Open / Close', href: '/dashboard/game-config/open-close' },
      { label: 'Bulk Mode', href: '/dashboard/game-config/bulk-mode' },
    ],
  },
  { title: 'Schedule', icon: 'calendar', items: [{ label: 'Market Schedule & Cutoffs', href: '/dashboard/schedule' }] },
  {
    title: 'Results',
    icon: 'check',
    items: [
      { label: "Today's Results", href: '/dashboard/results/today' },
      { label: 'Pending', href: '/dashboard/results/pending' },
      { label: 'Publish Result', href: '/dashboard/results/publish' },
      { label: 'Historical Results', href: '/dashboard/results/history' },
    ],
  },
  {
    title: 'Game Numbers',
    icon: 'chart',
    items: [{ label: 'Panel Chart (All Markets)', href: '/dashboard/game-numbers/panel-chart' }],
  },
  { title: 'Rates', icon: 'percent', items: [{ label: 'Simulated Rates', href: '/dashboard/rates' }] },
  {
    title: 'Simulations',
    icon: 'play',
    items: [
      { label: 'All Simulations', href: '/dashboard/simulations' },
      { label: 'Bulk Batches', href: '/dashboard/simulations/batches' },
      { label: 'User History', href: '/dashboard/simulations/history' },
    ],
  },
  {
    title: 'Users',
    icon: 'users',
    items: [{ label: 'All Users', href: '/dashboard/students' }],
  },
  {
    title: 'Wallet Activity',
    icon: 'coin',
    items: [
      { label: 'Overview', href: '/dashboard/wallet-activity' },
      { label: 'Payment Settings', href: '/dashboard/wallet-activity/payment-settings' },
      { label: 'Credit Requests', href: '/dashboard/wallet-activity/credit-requests' },
      { label: 'Learning Credits', href: '/dashboard/wallet-activity/credits' },
      { label: 'All Transactions', href: '/dashboard/wallet-activity/transactions' },
      { label: 'User Activity', href: '/dashboard/wallet-activity/activity' },
    ],
  },
  {
    title: 'Content',
    icon: 'file',
    items: [
      { label: 'Homepage', href: '/dashboard/content/homepage' },
      { label: 'Banners', href: '/dashboard/content/banners' },
      { label: 'Scrolling Messages', href: '/dashboard/content/scrolling' },
      { label: 'Game Guides', href: '/dashboard/content/educational' },
    ],
  },
  {
    title: 'Support',
    icon: 'support',
    items: [
      { label: 'Support Queries', href: '/dashboard/support/queries' },
      { label: 'Contact & WhatsApp', href: '/dashboard/support/contact' },
      { label: 'FAQ', href: '/dashboard/support/faq' },
    ],
  },
  {
    title: 'Reports',
    icon: 'chart',
    items: [
      { label: 'Simulation Statistics', permission: 'reports.view', href: '/dashboard/reports/simulation-statistics' },
      { label: 'Game Statistics', permission: 'reports.view', href: '/dashboard/reports/game-statistics' },
      { label: 'Number Frequency', permission: 'reports.view', href: '/dashboard/reports/number-frequency' },
      { label: 'Historical Charts', permission: 'reports.view', href: '/dashboard/reports/historical-charts' },
    ],
  },
  {
    title: 'System',
    icon: 'cog',
    items: [
      { label: 'Settings', href: '/dashboard/system/settings' },
      { label: 'Audit Logs', href: '/dashboard/system/audit-logs', permission: 'audit_logs.view' },
      { label: 'Admin Users', href: '/dashboard/system/admin-users', permission: 'admins.manage' },
      { label: 'Roles & Permissions', href: '/dashboard/system/roles' },
    ],
  },
];
