import { ErrorState, LinkButton } from '../components/ui'

export default function NotFound() {
  return <div className="p-8"><ErrorState title="Page not found" action={<LinkButton to="/app">Go to dashboard</LinkButton>}>This address doesn't match any page. Check the link or return to your dashboard.</ErrorState></div>
}
