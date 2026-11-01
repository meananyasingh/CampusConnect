import { BarChart3, BellRing, BriefcaseBusiness, Building2, CalendarClock, FileCheck2, LogOut, ShieldCheck, UserRoundCheck, UsersRound } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'

import NotificationBell from '../../components/NotificationBell.jsx'
import PortalActionGrid from '../../components/PortalActionGrid.jsx'
import { useAuth } from '../../hooks/useAuth.js'
import { placementService } from '../../services/placementService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

function CollegeAdminDashboardPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [signingOut, setSigningOut] = useState(false)
  const { logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    placementService.getAdminDashboard()
      .then(setData)
      .catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  const signOut = async () => {
    setSigningOut(true)
    await logout()
    navigate('/admin-login', { replace: true })
  }

  const stats = data ? [
    ['Students', data.total_students, UsersRound],
    ['Verified companies', data.verified_companies, Building2],
    ['Active opportunities', data.active_opportunities, BriefcaseBusiness],
    ['Applications', data.total_applications, FileCheck2],
    ['Shortlisted / interview', data.shortlisted_candidates, UserRoundCheck],
    ['Upcoming interviews', data.upcoming_interviews, CalendarClock],
    ['Placed students', data.placed_students, BarChart3],
    ['Placement percentage', `${data.placement_percentage}%`, BarChart3],
  ] : []

  return (
    <main className="dashboard-shell">
      <nav className="dashboard-nav">
        <div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div>
        <div className="d-flex align-items-center gap-2"><NotificationBell /><button className="btn btn-outline-secondary d-flex align-items-center gap-2" disabled={signingOut} onClick={signOut} type="button"><LogOut size={17} /> Sign out</button></div>
      </nav>
      <section className="container py-5">
        {loading ? <div className="text-center py-5"><div className="spinner-border text-primary" /></div> : data && <>
          <p className="eyebrow mb-2">College placement office</p>
          <h1 className="display-6 fw-bold mb-2">{data.college.name}</h1>
          <p className="text-secondary fs-5 mb-4">Live placement overview for {data.college.code}.</p>
          <div className="admin-stat-grid mb-4">{stats.map(([label, value, Icon]) => <article className="admin-stat-card" key={label}><span><Icon size={20} /></span><div><small>{label}</small><strong>{value}</strong></div></article>)}</div>
          <div className="row g-4 mb-4"><PackageCard label="Average annual package" value={data.average_package} /><PackageCard label="Highest annual package" value={data.highest_package} /></div>
          <PortalActionGrid items={adminActions} label="Placement operations" />
        </>}
      </section>
    </main>
  )
}

const adminActions = [
  { title: 'Opportunity requests', description: 'Review college invitations', icon: BriefcaseBusiness, to: '/admin/opportunity-requests' },
  { title: 'Student documents', description: 'Verify placement documents', icon: FileCheck2, to: '/admin/documents' },
  { title: 'Placement policy', description: 'Configure eligibility rules', icon: ShieldCheck, to: '/admin/policy' },
  { title: 'Placement drives', description: 'Plan and manage campus drives', icon: CalendarClock, to: '/admin/drives' },
  { title: 'Announcements', description: 'Publish important updates', icon: BellRing, to: '/admin/announcements' },
  { title: 'Placement records', description: 'Manage offers and outcomes', icon: BarChart3, to: '/admin/placements' },
  { title: 'Students', description: 'Manage student accounts', icon: UsersRound, to: '/admin/students' },
  { title: 'Import students', description: 'Create accounts in bulk', icon: UserRoundCheck, to: '/admin/student-imports' },
  { title: 'Analytics', description: 'Review reports and trends', icon: BarChart3, to: '/admin/analytics' },
  { title: 'Activity log', description: 'Audit important changes', icon: FileCheck2, to: '/admin/audit-log' },
  { title: 'Oversight', description: 'Applications and interviews', icon: CalendarClock, to: '/admin/oversight' },
  { title: 'Companies', description: 'Review recruiter companies', icon: Building2, to: '/admin/companies' },
]

function PackageCard({ label, value }) {
  return <div className="col-md-6"><article className="profile-card h-100"><p className="text-secondary small mb-1">{label}</p><h2 className="h3 fw-bold mb-0">{formatPackage(value)}</h2></article></div>
}

function formatPackage(value) {
  return value == null ? 'Not available' : new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value))
}

export default CollegeAdminDashboardPage
