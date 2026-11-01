import { BarChart3, BriefcaseBusiness, Building2, CalendarClock, FileCheck2, LogOut, Plus, UserRoundCheck, UsersRound } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link, useNavigate } from 'react-router-dom'

import NotificationBell from '../../components/NotificationBell.jsx'
import PortalActionGrid from '../../components/PortalActionGrid.jsx'
import { useAuth } from '../../hooks/useAuth.js'
import { analyticsService } from '../../services/analyticsService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

function RecruiterDashboardPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [signingOut, setSigningOut] = useState(false)
  const { logout, user } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    analyticsService.recruiterDashboard()
      .then(setData)
      .catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  const signOut = async () => { setSigningOut(true); await logout(); navigate('/recruiter/login', { replace: true }) }
  const stats = data ? [
    ['Active opportunities', data.stats.active_opportunities, BriefcaseBusiness],
    ['Total applicants', data.stats.total_applications, UsersRound],
    ['Under review', data.stats.under_review, FileCheck2],
    ['Shortlisted', data.stats.shortlisted, UserRoundCheck],
    ['Upcoming interviews', data.stats.upcoming_interviews, CalendarClock],
    ['Selected', data.stats.selected, BarChart3],
    ['Approved colleges', data.stats.verified_colleges, Building2],
  ] : []

  return <main className="dashboard-shell"><nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><div className="d-flex align-items-center gap-2"><NotificationBell /><button className="btn btn-outline-secondary d-flex align-items-center gap-2" disabled={signingOut} onClick={signOut} type="button"><LogOut size={17} /> Sign out</button></div></nav><section className="container py-5">{loading ? <Loading /> : data && <>
    <div className="dashboard-hero mb-4"><div><p className="eyebrow mb-2">Recruiter command center</p><h1 className="display-6 fw-bold mb-2">{data.company.name}</h1><p className="text-secondary mb-0">Welcome, {user.first_name || 'recruiter'}. Manage hiring activity across your approved colleges.</p></div><Link className="btn btn-primary d-flex align-items-center gap-2" to="/recruiter/opportunities"><Plus size={18} /> Create opportunity</Link></div>
    <div className="admin-stat-grid mb-4">{stats.map(([label, value, Icon]) => <article className="admin-stat-card" key={label}><span><Icon size={20} /></span><div><small>{label}</small><strong>{value}</strong></div></article>)}</div>
    <PortalActionGrid items={recruiterActions} />
    <div className="row g-4"><div className="col-12 col-xl-7"><Section action="All applicants" icon={UsersRound} title="Recent applicants" to="/recruiter/applications">{data.recent_applications.length ? <div className="dashboard-list">{data.recent_applications.map((item) => { const name = item.student.user.first_name || item.student.user.email; return <div className="dashboard-list-row" key={item.id}><span className="portfolio-icon"><UsersRound size={18} /></span><div className="flex-grow-1 min-width-0"><strong>{name}</strong><small>{item.opportunity.title} · {item.student.college_name}</small><span>CGPA {item.student.cgpa ?? 'not provided'} · Applied {formatDateTime(item.applied_at)}</span></div><span className={`application-status status-${item.status.toLowerCase().replace('_', '-')}`}>{item.status_display}</span></div> })}</div> : <Empty text="Applicants will appear after students apply." />}</Section></div>
    <div className="col-12 col-xl-5"><Section action="Manage hiring" icon={CalendarClock} title="Upcoming interviews" to="/recruiter/opportunities">{data.upcoming_interviews.length ? <div className="dashboard-list">{data.upcoming_interviews.map((item) => <div className="dashboard-list-row" key={item.id}><span className="portfolio-icon"><CalendarClock size={18} /></span><div><strong>{item.application.student.user.first_name || item.application.student.user.email}</strong><small>{item.recruitment_round.name} · {item.application.opportunity.title}</small><span>{formatDateTime(item.scheduled_at)} · {item.mode_display}</span></div></div>)}</div> : <Empty text="No upcoming candidate interviews." />}</Section></div>
    <div className="col-12"><Section action="Manage opportunities" icon={BarChart3} title="Opportunity performance" to="/recruiter/opportunities">{data.opportunity_performance.length ? <div className="table-responsive"><table className="table align-middle mb-0"><thead><tr><th>Opportunity</th><th>Status</th><th>Applicants</th><th>Shortlisted</th><th>Selected</th><th /></tr></thead><tbody>{data.opportunity_performance.map((item) => <tr key={item.id}><td className="fw-semibold">{item.title}</td><td><span className="badge text-bg-light">{item.status_display}</span></td><td>{item.total_applications}</td><td>{item.shortlisted}</td><td>{item.selected}</td><td className="text-end"><Link className="btn btn-sm btn-outline-primary" to={`/recruiter/applications?opportunity=${item.id}`}>View</Link></td></tr>)}</tbody></table></div> : <Empty text="Create your first opportunity to start recruiting." />}</Section></div></div>
  </>}</section></main>
}

const recruiterActions = [
  { title: 'Review applicants', description: 'Screen and progress candidates', icon: UsersRound, to: '/recruiter/applications' },
  { title: 'Discover talent', description: 'Search verified student profiles', icon: UserRoundCheck, to: '/recruiter/talent' },
  { title: 'Opportunities', description: 'Create and manage openings', icon: BriefcaseBusiness, to: '/recruiter/opportunities' },
  { title: 'Placement drives', description: 'View college hiring events', icon: CalendarClock, to: '/recruiter/drives' },
  { title: 'Announcements', description: 'Communicate with candidates', icon: FileCheck2, to: '/recruiter/announcements' },
  { title: 'Company and colleges', description: 'Manage profile and connections', icon: Building2, to: '/recruiter/company' },
]

function Section({ action, children, icon: Icon, title, to }) { return <section className="profile-card h-100"><div className="dashboard-section-title"><div><Icon size={19} /><h2>{title}</h2></div><Link to={to}>{action}</Link></div>{children}</section> }
function Empty({ text }) { return <div className="portfolio-empty">{text}</div> }
function Loading() { return <div className="text-center py-5"><div className="spinner-border text-primary" /></div> }
function formatDateTime(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) }

export default RecruiterDashboardPage
