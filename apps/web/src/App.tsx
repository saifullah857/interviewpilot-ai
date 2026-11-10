import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import PublicLayout from './layouts/PublicLayout'
import AppShell from './layouts/AppShell'
import { Spinner } from './components/ui'
import { AuthProvider, RequireAuth, RequireAdmin } from './lib/auth'
import Landing from './pages/Landing'
import { Login, Signup } from './pages/Auth'
import Dashboard from './pages/Dashboard'
import Companies from './pages/Companies'
import CompanyDetail from './pages/CompanyDetail'
import Resume from './pages/Resume'
import AssessmentSetup from './pages/Assessment'
import AssessmentPage from './pages/AssessmentPage'
import AssessmentTake from './pages/AssessmentTake'
import AssessmentReview from './pages/AssessmentReview'
import CodingList from './pages/CodingList'
import CodingReview from './pages/CodingReview'
import Voice from './pages/Voice'
import InterviewRoom from './pages/InterviewRoom'
import InterviewReview from './pages/InterviewReview'
import ReportView from './pages/ReportView'
import Progress from './pages/Progress'
import QuestionBank from './pages/QuestionBank'
import Readiness from './pages/Readiness'
import ScreeningResult from './pages/ScreeningResult'
import ScreeningSetup from './pages/ScreeningSetup'
import ScreeningTest from './pages/ScreeningTest'
import Results from './pages/Results'
import History from './pages/History'
import Settings from './pages/Settings'
import Admin from './pages/Admin'
import AdminQuestions from './pages/AdminQuestions'
import NotFound from './pages/NotFound'

// The coding session page (with the Monaco editor) is large, so it loads only when opened.
const CodingSession = lazy(() => import('./pages/CodingSession'))

export default function App() {
  return (
    <AuthProvider>
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
      </Route>
      <Route path="/app" element={<RequireAuth><AppShell /></RequireAuth>}>
        <Route index element={<Dashboard />} />
        <Route path="companies" element={<Companies />} />
        <Route path="companies/:slug" element={<CompanyDetail />} />
        <Route path="resume" element={<Resume />} />
        <Route path="assessment/setup" element={<AssessmentSetup />} />
        <Route path="assessment/:id" element={<AssessmentPage />} />
        <Route path="assessment/:id/take" element={<AssessmentTake />} />
        <Route path="assessment/:id/review" element={<AssessmentReview />} />
        <Route path="assessment/coding" element={<Navigate to="/app/coding" replace />} />
        <Route path="coding" element={<CodingList />} />
        <Route path="coding/:id" element={<Suspense fallback={<Spinner label="Loading the code editor" />}><CodingSession /></Suspense>} />
        <Route path="coding/:id/review" element={<CodingReview />} />
        <Route path="interview" element={<Voice />} />
        <Route path="interview/:id" element={<InterviewRoom />} />
        <Route path="interview/:id/review" element={<InterviewReview />} />
        <Route path="progress" element={<Progress />} />
        <Route path="questions" element={<QuestionBank />} />
        <Route path="readiness" element={<Readiness />} />
        <Route path="screening" element={<ScreeningSetup />} />
        <Route path="screening/:id" element={<ScreeningTest />} />
        <Route path="screening/:id/result" element={<ScreeningResult />} />
        <Route path="results" element={<Results />} />
        <Route path="results/:id" element={<ReportView />} />
        <Route path="history" element={<History />} />
        <Route path="settings" element={<Settings />} />
        <Route path="admin" element={<RequireAdmin><Admin /></RequireAdmin>} />
        <Route path="admin/questions" element={<RequireAdmin><AdminQuestions /></RequireAdmin>} />
        <Route path="*" element={<NotFound />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
    </AuthProvider>
  )
}
