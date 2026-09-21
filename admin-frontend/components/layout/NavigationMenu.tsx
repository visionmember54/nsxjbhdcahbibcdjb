'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { NAV_SECTIONS as ALL_SECTIONS, type NavSection } from './navConfig';
import { useCurrentAdmin } from '@/hooks/useAuth';
import { Icon } from './icons';

// Exact match, or a real sub-path (boundary on "/") -- a plain `startsWith`
// falsely activates a short href (e.g. "All Users" at /dashboard/students)
// for any page nested under it, even ones belonging to a different nav
// section. "/dashboard" itself is exact-only, since every route starts with it.
function isItemActive(pathname: string, href: string): boolean {
  if (pathname === href) return true;
  if (href === '/dashboard') return false;
  return pathname.startsWith(`${href}/`);
}

function sectionIsActive(section: NavSection, pathname: string) {
  return section.items.some((item) => isItemActive(pathname, item.href));
}

export default function NavigationMenu({ onNavigate, collapsed = false }: { onNavigate?: () => void; collapsed?: boolean }) {
  const pathname = usePathname();
  const [expanded, setExpanded] = useState<string[]>([]);
  const { data: me } = useCurrentAdmin();
  const NAV_SECTIONS = useMemo(
    () =>
      ALL_SECTIONS.map((s) => ({
        ...s,
        items: s.items.filter((i) => !i.permission || !me || me.permissions?.includes(i.permission)),
      })).filter((s) => s.items.length),
    [me],
  );

  useEffect(() => {
    const activeSection = NAV_SECTIONS.find((section) => section.title && sectionIsActive(section, pathname))?.title;
    if (activeSection) {
      setExpanded((current) => current.includes(activeSection) ? current : [...current, activeSection]);
    }
  }, [pathname, NAV_SECTIONS]);

  if (collapsed) {
    return (
      <nav className="sidebar-scroll flex-1 overflow-y-auto px-2.5 py-4" aria-label="Admin navigation">
        {NAV_SECTIONS.map((section) => {
          const active = sectionIsActive(section, pathname);
          const href = section.items[0].href;
          const label = section.title ?? section.items[0].label;
          return (
            <Link
              key={href}
              href={href}
              onClick={onNavigate}
              title={label}
              aria-label={label}
              className={`mb-1.5 flex h-11 w-full items-center justify-center rounded-lg transition-colors ${
                active
                  ? 'bg-gradient-to-r from-brand-500 to-brand-600 text-white shadow-glow'
                  : 'text-slate-400 hover:bg-white/5 hover:text-slate-100'
              }`}
            >
              <Icon name={section.icon} className="h-[18px] w-[18px]" />
            </Link>
          );
        })}
      </nav>
    );
  }

  return (
    <nav className="sidebar-scroll flex-1 overflow-y-auto px-3 py-4" aria-label="Admin navigation">
      {NAV_SECTIONS.map((section) => {
        const active = sectionIsActive(section, pathname);
        const isExpanded = section.title ? expanded.includes(section.title) : true;

        if (!section.title) {
          const item = section.items[0];
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={`mb-3 flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-semibold transition-colors ${
                active
                  ? 'bg-gradient-to-r from-brand-500 to-brand-600 text-white shadow-glow'
                  : 'text-slate-300 hover:bg-white/5 hover:text-white'
              }`}
            >
              <Icon name={section.icon} />
              {item.label}
            </Link>
          );
        }

        return (
          <section key={section.title} className="mb-0.5">
            <button
              type="button"
              onClick={() => setExpanded((current) => current.includes(section.title as string)
                ? current.filter((title) => title !== section.title)
                : [...current, section.title as string])}
              aria-expanded={isExpanded}
              className={`group flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-[13px] font-semibold transition-colors ${
                active ? 'text-white' : 'text-slate-400 hover:bg-white/5 hover:text-slate-100'
              }`}
            >
              <Icon name={section.icon} className={`h-[17px] w-[17px] shrink-0 ${active ? 'text-brand-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
              <span className="flex-1 truncate">{section.title}</span>
              <svg
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
                className={`h-3.5 w-3.5 shrink-0 text-slate-500 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
              >
                <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clipRule="evenodd" />
              </svg>
            </button>
            <div
              className="grid overflow-hidden transition-[grid-template-rows] duration-200 ease-out"
              style={{ gridTemplateRows: isExpanded ? '1fr' : '0fr' }}
            >
              <div className="min-h-0">
                <div className="relative ml-[22px] space-y-0.5 border-l border-white/10 py-1 pl-4">
                  {section.items.map((item) => {
                    const itemActive = isItemActive(pathname, item.href);
                    return (
                      <Link
                        key={`${item.label}-${item.href}`}
                        href={item.href}
                        onClick={onNavigate}
                        className={`relative block rounded-md px-2.5 py-1.5 text-[13px] transition-colors before:absolute before:-left-[17px] before:top-1/2 before:h-1.5 before:w-1.5 before:-translate-y-1/2 before:rounded-full before:transition-colors ${
                          itemActive
                            ? 'bg-white/10 font-semibold text-white before:bg-brand-400'
                            : 'text-slate-400 before:bg-slate-700 hover:bg-white/5 hover:text-slate-100 hover:before:bg-slate-500'
                        }`}
                      >
                        {item.label}
                      </Link>
                    );
                  })}
                </div>
              </div>
            </div>
          </section>
        );
      })}
    </nav>
  );
}
