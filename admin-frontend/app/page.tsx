'use client';

import Link from 'next/link';
import { useCurrentAdmin } from '@/hooks/useAuth';
import { Icon, type IconKey } from '@/components/layout/icons';

const NAV_LINKS = [
  { href: '#features', label: 'Features' },
  { href: '#workflow', label: 'Workflow' },
  { href: '#preview', label: 'Preview' },
  { href: '#faq', label: 'FAQ' },
];

const FEATURES: { icon: IconKey; title: string; description: string }[] = [
  { icon: 'market', title: 'Markets', description: 'Open, close, and schedule Matka, Starline, and Gali–Disawar markets from one control panel.' },
  { icon: 'check', title: 'Results', description: 'Publish and correct results with a full audit trail, and track pending declarations in real time.' },
  { icon: 'play', title: 'Simulations', description: 'Review every simulated entry, override outcomes, and manage bulk simulation batches.' },
  { icon: 'chart', title: 'Reports', description: 'Drill into simulation statistics, number frequency, and historical performance by market.' },
  { icon: 'users', title: 'Users', description: 'Manage learner accounts, virtual learning credits, and activity — all in one directory.' },
  { icon: 'sliders', title: 'Configuration', description: 'Fine-tune rates, cutoffs, and game-type rules for Single, Jodi, Panna, and Sangam formats.' },
];

const HIGHLIGHTS: { icon: IconKey; label: string }[] = [
  { icon: 'cog', label: 'Role-based admin access' },
  { icon: 'file', label: 'Audit-ready action logs' },
  { icon: 'calendar', label: 'Live cutoff scheduling' },
  { icon: 'support', label: 'Built-in support workflows' },
];

const WORKFLOW: { icon: IconKey; step: string; title: string; description: string }[] = [
  { icon: 'sliders', step: '01', title: 'Configure & schedule', description: 'Set rates, cutoffs, and game-type rules, then schedule markets to open and close automatically.' },
  { icon: 'play', step: '02', title: 'Run & monitor', description: 'Watch simulations come in live, track pending entries, and step in to override an outcome if needed.' },
  { icon: 'check', step: '03', title: 'Publish & report', description: 'Declare results with a full audit trail, then hand off clean statistics to your reporting workflow.' },
];

const FAQS: { question: string; answer: string }[] = [
  { question: 'Is this real-money gambling?', answer: 'No. Kalyan Admin runs an educational simulator that uses virtual Learning Credits only — there are no real-money transactions anywhere in the platform.' },
  { question: 'Who is the console built for?', answer: 'Operations teams running the simulator day-to-day: the people scheduling markets, declaring results, reviewing simulations, and supporting learners.' },
  { question: 'Can I control who sees what?', answer: 'Yes. Admin accounts carry roles and permissions, and every sensitive action — logins, publishes, corrections — is written to an audit log.' },
  { question: 'How are results corrected if something goes wrong?', answer: 'Published results can be corrected from the Results screen; the original and corrected values are both preserved in the audit trail.' },
  { question: 'Does it cover Starline and Gali–Disawar too, or just the main markets?', answer: 'All of them. Matka, Starline, and Gali–Disawar markets are managed side-by-side in the same console.' },
];

function PreviewNavItem({ icon, label, active = false }: { icon: IconKey; label: string; active?: boolean }) {
  return (
    <div className={`flex items-center gap-2 rounded-md px-2.5 py-1.5 text-[11px] font-medium ${active ? 'bg-white/10 text-white' : 'text-slate-400'}`}>
      <Icon name={icon} className="h-3.5 w-3.5" />
      {label}
    </div>
  );
}

export default function HomePage() {
  const { data: admin } = useCurrentAdmin();
  const ctaHref = admin ? '/dashboard' : '/login';
  const ctaLabel = admin ? 'Go to Dashboard' : 'Sign in to Console';

  return (
    <div className="min-h-screen bg-white font-sans">
      {/* Nav */}
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-brand-400 to-brand-600 text-sm font-bold text-white shadow-glow">
              K
            </div>
            <span className="text-sm font-bold tracking-tight text-slate-950">Kalyan Admin</span>
          </div>

          <nav className="hidden items-center gap-7 md:flex" aria-label="Section navigation">
            {NAV_LINKS.map((link) => (
              <a key={link.href} href={link.href} className="text-sm font-medium text-slate-600 transition-colors hover:text-slate-950">
                {link.label}
              </a>
            ))}
          </nav>

          <Link
            href={ctaHref}
            className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-b from-brand-500 to-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-glow transition-all hover:from-brand-400 hover:to-brand-500 active:scale-[0.98]"
          >
            {ctaLabel}
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden bg-ink-950">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute inset-0 bg-gradient-to-br from-brand-950 via-ink-950 to-ink-900" />
          <div className="absolute -left-24 -top-24 h-80 w-80 rounded-full bg-brand-500/20 blur-3xl" />
          <div className="absolute -bottom-32 -right-20 h-96 w-96 rounded-full bg-brand-400/10 blur-3xl" />
          <div
            className="absolute inset-0 opacity-[0.06]"
            style={{ backgroundImage: 'radial-gradient(circle, #ffffff 1px, transparent 1px)', backgroundSize: '28px 28px' }}
          />
        </div>

        <div className="relative mx-auto max-w-6xl px-5 py-24 text-center sm:py-32">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-brand-200">
            Operations console for Kalyan Simulator
          </span>
          <h1 className="mx-auto mt-6 max-w-2xl text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Run every market, result, and simulation from one place
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-slate-400">
            A single console for managing markets, publishing results, reviewing simulations, and supporting
            learners — built for teams operating the Kalyan educational simulator.
          </p>
          <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
            <Link
              href={ctaHref}
              className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-b from-brand-500 to-brand-600 px-5 py-3 text-sm font-semibold text-white shadow-glow transition-all hover:from-brand-400 hover:to-brand-500 active:scale-[0.98]"
            >
              {ctaLabel}
              <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l5 5a1 1 0 010 1.414l-5 5a1 1 0 01-1.414-1.414L13.586 10H4a1 1 0 110-2h9.586l-3.293-3.293a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </Link>
            <a
              href="#workflow"
              className="inline-flex items-center gap-1.5 rounded-lg border border-white/15 bg-white/5 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/10"
            >
              See how it works
            </a>
          </div>

          <div className="mx-auto mt-14 flex max-w-3xl flex-wrap items-center justify-center gap-x-8 gap-y-3">
            {HIGHLIGHTS.map((item) => (
              <div key={item.label} className="flex items-center gap-2 text-sm text-slate-300">
                <Icon name={item.icon} className="h-4 w-4 text-brand-400" />
                {item.label}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto max-w-6xl scroll-mt-20 px-5 py-20">
        <div className="mx-auto max-w-xl text-center">
          <span className="text-xs font-semibold uppercase tracking-wide text-brand-600">Features</span>
          <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">Everything operations needs, in one console</h2>
          <p className="mt-3 text-sm text-slate-500">
            From market scheduling to payout reporting, the console mirrors how your team actually works.
          </p>
        </div>

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="group rounded-xl border border-slate-200/80 bg-white p-5 shadow-soft transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card"
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                <Icon name={feature.icon} className="h-5 w-5" />
              </span>
              <h3 className="mt-4 text-sm font-semibold text-slate-900">{feature.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-500">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Workflow */}
      <section id="workflow" className="scroll-mt-20 bg-slate-50 px-5 py-20">
        <div className="mx-auto max-w-6xl">
          <div className="mx-auto max-w-xl text-center">
            <span className="text-xs font-semibold uppercase tracking-wide text-brand-600">Workflow</span>
            <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">From scheduling to reporting, in three steps</h2>
            <p className="mt-3 text-sm text-slate-500">The console is built around how a market actually moves through its day.</p>
          </div>

          <div className="relative mt-14 grid gap-8 sm:grid-cols-3">
            <div className="pointer-events-none absolute left-0 right-0 top-6 hidden h-px bg-slate-200 sm:block" aria-hidden="true" />
            {WORKFLOW.map((item) => (
              <div key={item.step} className="relative text-center sm:text-left">
                <div className="relative z-10 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-600 text-white shadow-glow sm:mx-0 mx-auto">
                  <Icon name={item.icon} className="h-5 w-5" />
                </div>
                <p className="mt-4 text-xs font-bold tracking-wide text-brand-600">STEP {item.step}</p>
                <h3 className="mt-1 text-base font-semibold text-slate-900">{item.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-slate-500">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Product preview */}
      <section id="preview" className="mx-auto max-w-6xl scroll-mt-20 px-5 py-20">
        <div className="mx-auto max-w-xl text-center">
          <span className="text-xs font-semibold uppercase tracking-wide text-brand-600">Preview</span>
          <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">A console that stays out of your way</h2>
          <p className="mt-3 text-sm text-slate-500">Dark, focused navigation on the side; live numbers and clear tables where you need them.</p>
        </div>

        <div className="mx-auto mt-12 max-w-4xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
          <div className="flex items-center gap-1.5 border-b border-slate-200 bg-slate-50 px-4 py-2.5">
            <span className="h-2.5 w-2.5 rounded-full bg-red-400" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
            <span className="ml-3 rounded-md bg-white px-2.5 py-1 text-[11px] text-slate-400 ring-1 ring-inset ring-slate-200">kalyan-admin/dashboard</span>
          </div>

          <div className="flex">
            <div className="hidden w-40 shrink-0 bg-sidebar-gradient p-3 sm:block">
              <div className="mb-3 flex items-center gap-1.5 px-1">
                <div className="flex h-5 w-5 items-center justify-center rounded-md bg-gradient-to-br from-brand-400 to-brand-600 text-[9px] font-bold text-white">K</div>
                <span className="text-[10px] font-bold text-white">Kalyan Admin</span>
              </div>
              <div className="space-y-1">
                <PreviewNavItem icon="home" label="Dashboard" active />
                <PreviewNavItem icon="market" label="Markets" />
                <PreviewNavItem icon="check" label="Results" />
                <PreviewNavItem icon="play" label="Simulations" />
                <PreviewNavItem icon="users" label="Users" />
                <PreviewNavItem icon="chart" label="Reports" />
              </div>
            </div>

            <div className="flex-1 bg-slate-50 p-4 sm:p-5">
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: 'Open Markets', value: '3', icon: 'market' as IconKey, tone: 'text-emerald-600 bg-emerald-50' },
                  { label: 'Simulations', value: '23', icon: 'play' as IconKey, tone: 'text-purple-600 bg-purple-50' },
                  { label: 'Credits Staked', value: '1,215', icon: 'coin' as IconKey, tone: 'text-brand-600 bg-brand-50' },
                ].map((tile) => (
                  <div key={tile.label} className="rounded-lg border border-slate-200 bg-white p-3 shadow-soft">
                    <span className={`inline-flex h-6 w-6 items-center justify-center rounded-md ${tile.tone}`}>
                      <Icon name={tile.icon} className="h-3.5 w-3.5" />
                    </span>
                    <p className="mt-2 text-[10px] font-medium uppercase tracking-wide text-slate-400">{tile.label}</p>
                    <p className="text-sm font-bold text-slate-900">{tile.value}</p>
                  </div>
                ))}
              </div>

              <div className="mt-3 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-soft">
                <div className="border-b border-slate-100 bg-slate-50/80 px-3 py-2 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                  Today by market
                </div>
                {['MILAN DAY', 'RAJDHANI DAY', 'GALI'].map((market, i) => (
                  <div key={market} className={`flex items-center justify-between px-3 py-2 text-[11px] ${i !== 2 ? 'border-b border-slate-100' : ''}`}>
                    <span className="font-medium text-slate-700">{market}</span>
                    <span className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-100">
                      <span className="block h-full rounded-full bg-brand-400" style={{ width: `${60 - i * 15}%` }} />
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="scroll-mt-20 bg-slate-50 px-5 py-20">
        <div className="mx-auto max-w-2xl">
          <div className="text-center">
            <span className="text-xs font-semibold uppercase tracking-wide text-brand-600">FAQ</span>
            <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">Frequently asked questions</h2>
          </div>

          <div className="mt-10 space-y-3">
            {FAQS.map((faq) => (
              <details key={faq.question} className="group rounded-xl border border-slate-200 bg-white p-4 shadow-soft open:shadow-card">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-sm font-semibold text-slate-900 [&::-webkit-details-marker]:hidden">
                  {faq.question}
                  <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4 shrink-0 text-slate-400 transition-transform duration-200 group-open:rotate-180">
                    <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clipRule="evenodd" />
                  </svg>
                </summary>
                <p className="mt-3 text-sm leading-relaxed text-slate-500">{faq.answer}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* CTA banner */}
      <section className="mx-auto max-w-6xl px-5 py-20">
        <div className="relative overflow-hidden rounded-2xl bg-sidebar-gradient px-8 py-12 text-center shadow-card sm:py-16">
          <div
            className="pointer-events-none absolute inset-0 opacity-[0.06]"
            style={{ backgroundImage: 'radial-gradient(circle, #ffffff 1px, transparent 1px)', backgroundSize: '24px 24px' }}
          />
          <div className="relative">
            <h2 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">Ready to get into the console?</h2>
            <p className="mx-auto mt-3 max-w-md text-sm text-slate-400">
              Sign in with your admin credentials to manage today&rsquo;s markets and results.
            </p>
            <Link
              href={ctaHref}
              className="mt-7 inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-b from-brand-500 to-brand-600 px-5 py-3 text-sm font-semibold text-white shadow-glow transition-all hover:from-brand-400 hover:to-brand-500 active:scale-[0.98]"
            >
              {ctaLabel}
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 px-5 py-12">
        <div className="mx-auto grid max-w-6xl gap-10 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-400 to-brand-600 text-xs font-bold text-white">K</div>
              <span className="text-sm font-bold tracking-tight text-slate-950">Kalyan Admin</span>
            </div>
            <p className="mt-3 max-w-xs text-xs leading-relaxed text-slate-400">
              The operations console for the Kalyan educational simulator — virtual credits only.
            </p>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Console</p>
            <ul className="mt-3 space-y-2 text-sm text-slate-600">
              <li><a href="#features" className="hover:text-slate-950">Features</a></li>
              <li><a href="#workflow" className="hover:text-slate-950">Workflow</a></li>
              <li><a href="#preview" className="hover:text-slate-950">Preview</a></li>
            </ul>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Support</p>
            <ul className="mt-3 space-y-2 text-sm text-slate-600">
              <li><a href="#faq" className="hover:text-slate-950">FAQ</a></li>
              <li><Link href="/login" className="hover:text-slate-950">Admin sign in</Link></li>
            </ul>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Legal</p>
            <p className="mt-3 text-xs leading-relaxed text-slate-400">
              Educational simulator. Virtual Learning Credits only — no real-money transactions.
            </p>
          </div>
        </div>

        <div className="mx-auto mt-10 max-w-6xl border-t border-slate-100 pt-6 text-center text-xs text-slate-400">
          &copy; {new Date().getFullYear()} Kalyan Admin. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
