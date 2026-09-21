export type IconKey =
  | 'home'
  | 'market'
  | 'sliders'
  | 'calendar'
  | 'check'
  | 'percent'
  | 'play'
  | 'users'
  | 'file'
  | 'support'
  | 'chart'
  | 'cog'
  | 'coin'
  | 'clock';

const paths: Record<IconKey, React.ReactNode> = {
  home: (
    <>
      <path d="M3.5 10.5 12 3l8.5 7.5" />
      <path d="M5.5 9.5V20a1 1 0 0 0 1 1H10v-6h4v6h3.5a1 1 0 0 0 1-1V9.5" />
    </>
  ),
  market: (
    <>
      <path d="M4 8.5 5 4h14l1 4.5" />
      <path d="M3.5 8.5h17" />
      <path d="M4.5 8.5V20a1 1 0 0 0 1 1H9v-6h6v6h3.5a1 1 0 0 0 1-1V8.5" />
    </>
  ),
  sliders: (
    <>
      <path d="M4 6h9" />
      <path d="M17 6h3" />
      <circle cx="14.5" cy="6" r="2" />
      <path d="M4 12h3" />
      <path d="M11 12h9" />
      <circle cx="8.5" cy="12" r="2" />
      <path d="M4 18h11" />
      <path d="M19 18h1" />
      <circle cx="17.5" cy="18" r="2" />
    </>
  ),
  calendar: (
    <>
      <rect x="3.5" y="5" width="17" height="15.5" rx="2" />
      <path d="M8 3v4" />
      <path d="M16 3v4" />
      <path d="M3.5 10h17" />
    </>
  ),
  check: (
    <>
      <path d="M7 4a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1V4Z" />
      <path d="M9.5 3.5h5a.5.5 0 0 1 .5.5v1a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1V4a.5.5 0 0 1 .5-.5Z" />
      <path d="m9.5 13 2 2 4-4" />
    </>
  ),
  percent: (
    <>
      <circle cx="6.5" cy="6.5" r="2.5" />
      <circle cx="17.5" cy="17.5" r="2.5" />
      <path d="M19 5 5 19" />
    </>
  ),
  play: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M10 8.5v7l6-3.5-6-3.5Z" />
    </>
  ),
  users: (
    <>
      <circle cx="9" cy="8.5" r="3" />
      <path d="M3 20c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5" />
      <circle cx="17" cy="9" r="2.3" />
      <path d="M16 14.5c2.5.4 4.5 2.2 4.5 5.5" />
    </>
  ),
  file: (
    <>
      <path d="M6.5 3h7l4 4v13a1 1 0 0 1-1 1h-10a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
      <path d="M13.5 3v4h4" />
      <path d="M9 13h6" />
      <path d="M9 17h6" />
    </>
  ),
  support: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <circle cx="12" cy="12" r="3" />
      <path d="m6.1 6.1 3.3 3.3" />
      <path d="m14.6 14.6 3.3 3.3" />
      <path d="m17.9 6.1-3.3 3.3" />
      <path d="m9.4 14.6-3.3 3.3" />
    </>
  ),
  chart: (
    <>
      <path d="M4 20V10" />
      <path d="M4 20h16" />
      <rect x="4" y="13" width="3.2" height="7" />
      <rect x="10.4" y="9" width="3.2" height="11" />
      <rect x="16.8" y="5" width="3.2" height="15" />
    </>
  ),
  cog: (
    <>
      <circle cx="12" cy="12" r="3.2" />
      <path d="M12 3.5v2.2M12 18.3v2.2M20.5 12h-2.2M5.7 12H3.5M17.8 6.2l-1.6 1.6M7.8 16.2l-1.6 1.6M17.8 17.8l-1.6-1.6M7.8 7.8 6.2 6.2" />
    </>
  ),
  coin: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5v9" />
      <path d="M15 9.8c0-1.3-1.3-2.3-3-2.3s-3 .9-3 2.1c0 3 6 1.4 6 4.4 0 1.2-1.3 2.1-3 2.1s-3-1-3-2.3" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7v5.3l3.8 2.2" />
    </>
  ),
};

export function Icon({ name, className = 'h-[18px] w-[18px]' }: { name: IconKey; className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}
