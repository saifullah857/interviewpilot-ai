import { useState } from 'react'
import { NavLink, Outlet, Link, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Building2, FileText, ClipboardList, Code2, Mic, BarChart3, History, Settings, Menu, X, Navigation, LogOut, ShieldCheck, TrendingUp } from 'lucide-react'
import { cx } from '../components/ui'
import { useAuth } from '../lib/auth'

const NAV = [
  { to: '/app', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/app/companies', label: 'Lahore companies', icon: Building2 },
  { to: '/app/resume', label: 'Resume', icon: FileText },
  { to: '/app/assessment/setup', label: 'Practice', icon: ClipboardList },
  { to: '/app/coding', label: 'Coding', icon: Code2 },
  { to: '/app/interview', label: 'Voice interview', icon: Mic },
  { to: '/app/readiness', label: 'Company readiness', icon: BarChart3 },
  { to: '/app/screening', label: 'Online screening', icon: ClipboardList },
  { to: '/app/questions', label: 'Question bank', icon: ClipboardList },
  { to: '/app/progress', label: 'My progress', icon: TrendingUp },
  { to: '/app/results', label: 'Results', icon: BarChart3 },
  { to: '/app/history', label: 'History', icon: History },
  { to: '/app/settings', label: 'Settings', icon: Settings },
]

export function Logo({ light }: { light?: boolean }) {
  return (
    <Link to="/" className={cx('flex items-center gap-2 font-display text-lg font-bold', light ? 'text-white' : 'text-ink')}>
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-ink" aria-hidden><Navigation size={16} /></span>
      InterviewPilot AI
    </Link>
  )
}

export default function AppShell() {
  const [open, setOpen] = useState(false)
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const signOut = async () => { await logout(); navigate('/login', { replace: true }) }
  const items = user?.role === 'admin' ? [...NAV, { to: '/app/admin', label: 'Company review', icon: ShieldCheck, end: true }, { to: '/app/admin/questions', label: 'Manage questions', icon: ShieldCheck, end: false }] : NAV
  const nav = (
    <nav aria-label="Main" className="flex flex-col gap-1">
      {items.map(({ to, label, icon: Icon, end }) => (
        <NavLink key={to} to={to} end={end} onClick={() => setOpen(false)}
          className={({ isActive }) => cx('flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm', isActive ? 'bg-brand text-ink font-semibold' : 'text-slate-200 hover:bg-deck-raised')}>
          <Icon size={18} aria-hidden /> {label}
        </NavLink>
      ))}
    </nav>
  )
  return (
    <div className="min-h-screen lg:flex">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:m-2 focus:rounded focus:bg-white focus:p-2">Skip to content</a>
      <aside className="hidden w-64 shrink-0 flex-col gap-8 bg-deck p-5 lg:flex">
        <Logo light />
        {nav}
        <div className="mt-auto space-y-3">
          <p className="truncate text-sm text-slate-300" title={user?.email}>{user?.profile.display_name || user?.email}</p>
          <button onClick={signOut} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-200 hover:bg-deck-raised"><LogOut size={16} aria-hidden /> Log out</button>
          <p className="text-xs text-slate-400">Practice scores are preparation indicators, not hiring predictions.</p>
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between gap-3 border-b border-line bg-surface px-4 py-3 lg:px-8">
          <button className="rounded-lg p-2 lg:hidden" aria-label={open ? 'Close menu' : 'Open menu'} aria-expanded={open} onClick={() => setOpen(!open)}>
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className="lg:hidden"><Logo /></div>
          <p className="text-xs text-ink-mute">Practice tool: scores are preparation indicators, not hiring predictions.</p>
        </header>
        {open && <div className="bg-deck p-4 lg:hidden">{nav}<button onClick={signOut} className="mt-2 flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-sm text-slate-200 hover:bg-deck-raised"><LogOut size={16} aria-hidden /> Log out</button></div>}
        <main id="main" className="mx-auto w-full max-w-6xl flex-1 p-4 lg:p-8"><Outlet /></main>
      </div>
    </div>
  )
}
