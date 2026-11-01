import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'

import './App.css'
import RoleProtectedRoute from './components/RoleProtectedRoute.jsx'

const AuthPage = lazy(() => import('./pages/auth/AuthPage.jsx'))
const AnnouncementManagementPage = lazy(() => import('./pages/dashboard/AnnouncementManagementPage.jsx'))
const CollegeAdminDashboardPage = lazy(() => import('./pages/admin/CollegeAdminDashboardPage.jsx'))
const CollegeAnalyticsPage = lazy(() => import('./pages/admin/CollegeAnalyticsPage.jsx'))
const CollegeAuditLogPage = lazy(() => import('./pages/admin/CollegeAuditLogPage.jsx'))
const CollegeDrivesPage = lazy(() => import('./pages/admin/CollegeDrivesPage.jsx'))
const CollegeOversightPage = lazy(() => import('./pages/admin/CollegeOversightPage.jsx'))
const CollegePlacementsPage = lazy(() => import('./pages/admin/CollegePlacementsPage.jsx'))
const CollegePlacementPolicyPage = lazy(() => import('./pages/admin/CollegePlacementPolicyPage.jsx'))
const CollegeStudentsPage = lazy(() => import('./pages/admin/CollegeStudentsPage.jsx'))
const CollegeStudentImportPage = lazy(() => import('./pages/admin/CollegeStudentImportPage.jsx'))
const CompanyVerificationPage = lazy(() => import('./pages/admin/CompanyVerificationPage.jsx'))
const DocumentVerificationPage = lazy(() => import('./pages/admin/DocumentVerificationPage.jsx'))
const RecruiterDashboardPage = lazy(() => import('./pages/recruiter/RecruiterDashboardPage.jsx'))
const StudentDashboardPage = lazy(() => import('./pages/student/StudentDashboardPage.jsx'))
const StudentDocumentsPage = lazy(() => import('./pages/student/StudentDocumentsPage.jsx'))
const ForgotPasswordPage = lazy(() => import('./pages/auth/ForgotPasswordPage.jsx'))
const HomePage = lazy(() => import('./pages/public/HomePage.jsx'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage.jsx'))
const NotificationsPage = lazy(() => import('./pages/NotificationsPage.jsx'))
const OpportunityRequestsPage = lazy(() => import('./pages/admin/OpportunityRequestsPage.jsx'))
const PlacementDrivesPage = lazy(() => import('./pages/dashboard/PlacementDrivesPage.jsx'))
const RecruiterApplicationsPage = lazy(() => import('./pages/recruiter/RecruiterApplicationsPage.jsx'))
const RecruiterCompanyPage = lazy(() => import('./pages/recruiter/RecruiterCompanyPage.jsx'))
const RecruiterOpportunitiesPage = lazy(() => import('./pages/recruiter/RecruiterOpportunitiesPage.jsx'))
const RecruiterTalentPage = lazy(() => import('./pages/recruiter/RecruiterTalentPage.jsx'))
const RecruitmentProcessPage = lazy(() => import('./pages/recruiter/RecruitmentProcessPage.jsx'))
const ResetPasswordPage = lazy(() => import('./pages/auth/ResetPasswordPage.jsx'))
const StudentApplicationsPage = lazy(() => import('./pages/student/StudentApplicationsPage.jsx'))
const StudentAnnouncementsPage = lazy(() => import('./pages/student/StudentAnnouncementsPage.jsx'))
const StudentInterviewsPage = lazy(() => import('./pages/student/StudentInterviewsPage.jsx'))
const StudentOpportunitiesPage = lazy(() => import('./pages/student/StudentOpportunitiesPage.jsx'))
const StudentPlacementsPage = lazy(() => import('./pages/student/StudentPlacementsPage.jsx'))
const StudentPlacementReadinessPage = lazy(() => import('./pages/student/StudentPlacementReadinessPage.jsx'))
const StudentPortfolioPage = lazy(() => import('./pages/student/StudentPortfolioPage.jsx'))
const StudentProfilePage = lazy(() => import('./pages/student/StudentProfilePage.jsx'))
const StudentResumePage = lazy(() => import('./pages/student/StudentResumePage.jsx'))

function App() {
  return (
    <Suspense fallback={<main className="site-shell d-flex align-items-center justify-content-center"><div className="spinner-border text-primary"><span className="visually-hidden">Loading page…</span></div></main>}><Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/student/login" element={<AuthPage mode="login" role="STUDENT" />} />
      <Route path="/student/signup" element={<AuthPage mode="signup" role="STUDENT" />} />
      <Route path="/recruiter/login" element={<AuthPage mode="login" role="RECRUITER" />} />
      <Route path="/recruiter/signup" element={<AuthPage mode="signup" role="RECRUITER" />} />
      <Route path="/admin-login" element={<AuthPage mode="login" role="ADMIN" />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password/:uid/:token" element={<ResetPasswordPage />} />
      <Route path="/activate-account/:uid/:token" element={<ResetPasswordPage activation />} />
      <Route path="/notifications" element={<RoleProtectedRoute><NotificationsPage /></RoleProtectedRoute>} />
      <Route
        path="/student/dashboard"
        element={<RoleProtectedRoute role="STUDENT"><StudentDashboardPage /></RoleProtectedRoute>}
      />
      <Route
        path="/student/profile"
        element={
          <RoleProtectedRoute role="STUDENT">
            <StudentProfilePage />
          </RoleProtectedRoute>
        }
      />
      <Route
        path="/student/portfolio"
        element={
          <RoleProtectedRoute role="STUDENT">
            <StudentPortfolioPage />
          </RoleProtectedRoute>
        }
      />
      <Route
        path="/student/resumes"
        element={
          <RoleProtectedRoute role="STUDENT">
            <StudentResumePage />
          </RoleProtectedRoute>
        }
      />
      <Route path="/student/opportunities" element={<RoleProtectedRoute role="STUDENT"><StudentOpportunitiesPage /></RoleProtectedRoute>} />
      <Route path="/student/applications" element={<RoleProtectedRoute role="STUDENT"><StudentApplicationsPage /></RoleProtectedRoute>} />
      <Route path="/student/announcements" element={<RoleProtectedRoute role="STUDENT"><StudentAnnouncementsPage /></RoleProtectedRoute>} />
      <Route path="/student/interviews" element={<RoleProtectedRoute role="STUDENT"><StudentInterviewsPage /></RoleProtectedRoute>} />
      <Route path="/student/drives" element={<RoleProtectedRoute role="STUDENT"><PlacementDrivesPage role="STUDENT" /></RoleProtectedRoute>} />
      <Route path="/student/placements" element={<RoleProtectedRoute role="STUDENT"><StudentPlacementsPage /></RoleProtectedRoute>} />
      <Route path="/student/readiness" element={<RoleProtectedRoute role="STUDENT"><StudentPlacementReadinessPage /></RoleProtectedRoute>} />
      <Route path="/student/documents" element={<RoleProtectedRoute role="STUDENT"><StudentDocumentsPage /></RoleProtectedRoute>} />
      <Route
        path="/recruiter/dashboard"
        element={<RoleProtectedRoute role="RECRUITER"><RecruiterDashboardPage /></RoleProtectedRoute>}
      />
      <Route
        path="/recruiter/company"
        element={<RoleProtectedRoute role="RECRUITER"><RecruiterCompanyPage /></RoleProtectedRoute>}
      />
      <Route path="/recruiter/opportunities" element={<RoleProtectedRoute role="RECRUITER"><RecruiterOpportunitiesPage /></RoleProtectedRoute>} />
      <Route path="/recruiter/talent" element={<RoleProtectedRoute role="RECRUITER"><RecruiterTalentPage /></RoleProtectedRoute>} />
      <Route path="/recruiter/applications" element={<RoleProtectedRoute role="RECRUITER"><RecruiterApplicationsPage /></RoleProtectedRoute>} />
      <Route path="/recruiter/announcements" element={<RoleProtectedRoute role="RECRUITER"><AnnouncementManagementPage role="RECRUITER" /></RoleProtectedRoute>} />
      <Route path="/recruiter/drives" element={<RoleProtectedRoute role="RECRUITER"><PlacementDrivesPage role="RECRUITER" /></RoleProtectedRoute>} />
      <Route path="/recruiter/opportunities/:opportunityId/process" element={<RoleProtectedRoute role="RECRUITER"><RecruitmentProcessPage /></RoleProtectedRoute>} />
      <Route
        path="/admin-dashboard"
        element={<RoleProtectedRoute role="ADMIN"><CollegeAdminDashboardPage /></RoleProtectedRoute>}
      />
      <Route
        path="/admin/companies"
        element={<RoleProtectedRoute role="ADMIN"><CompanyVerificationPage /></RoleProtectedRoute>}
      />
      <Route path="/admin/opportunity-requests" element={<RoleProtectedRoute role="ADMIN"><OpportunityRequestsPage /></RoleProtectedRoute>} />
      <Route path="/admin/documents" element={<RoleProtectedRoute role="ADMIN"><DocumentVerificationPage /></RoleProtectedRoute>} />
      <Route path="/admin/announcements" element={<RoleProtectedRoute role="ADMIN"><AnnouncementManagementPage role="ADMIN" /></RoleProtectedRoute>} />
      <Route path="/admin/oversight" element={<RoleProtectedRoute role="ADMIN"><CollegeOversightPage /></RoleProtectedRoute>} />
      <Route path="/admin/placements" element={<RoleProtectedRoute role="ADMIN"><CollegePlacementsPage /></RoleProtectedRoute>} />
      <Route path="/admin/policy" element={<RoleProtectedRoute role="ADMIN"><CollegePlacementPolicyPage /></RoleProtectedRoute>} />
      <Route path="/admin/drives" element={<RoleProtectedRoute role="ADMIN"><CollegeDrivesPage /></RoleProtectedRoute>} />
      <Route path="/admin/students" element={<RoleProtectedRoute role="ADMIN"><CollegeStudentsPage /></RoleProtectedRoute>} />
      <Route path="/admin/student-imports" element={<RoleProtectedRoute role="ADMIN"><CollegeStudentImportPage /></RoleProtectedRoute>} />
      <Route path="/admin/analytics" element={<RoleProtectedRoute role="ADMIN"><CollegeAnalyticsPage /></RoleProtectedRoute>} />
      <Route path="/admin/audit-log" element={<RoleProtectedRoute role="ADMIN"><CollegeAuditLogPage /></RoleProtectedRoute>} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes></Suspense>
  )
}

export default App
