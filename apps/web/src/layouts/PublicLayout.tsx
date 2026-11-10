import { Outlet } from 'react-router-dom'
import { Logo } from './AppShell'
import { LinkButton } from '../components/ui'

export default function PublicLayout() {
  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between px-4 py-4 lg:px-10">
        <Logo />
        <nav aria-label="Account" className="flex gap-2">
          <LinkButton to="/login" variant="ghost">Log in</LinkButton>
          <LinkButton to="/signup">Sign up</LinkButton>
        </nav>
      </header>
      <main><Outlet /></main>
      <footer className="mt-16 border-t border-line px-4 py-6 text-sm text-ink-mute lg:px-10">
        InterviewPilot AI is a preparation tool. It does not make hiring decisions, and scores are not predictions of selection.
      </footer>
    </div>
  )
}
