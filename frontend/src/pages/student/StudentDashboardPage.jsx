import { Award, BellRing, BriefcaseBusiness, CalendarClock, FileCheck2, LogOut, Sparkles, Target, UserRoundCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link, useNavigate } from 'react-router-dom'

import NotificationBell from '../../components/NotificationBell.jsx'
import PortalActionGrid from '../../components/PortalActionGrid.jsx'
import { useAuth } from '../../hooks/useAuth.js'
import { analyticsService } from '../../services/analyticsService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

function StudentDashboardPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [signingOut, setSigningOut] = useState(false)
  const { logout, user } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    analyticsService.studentDashboard()
      .then(setData)
      .catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  const signOut = async () => {
    setSigningOut(true)
    await logout()
    navigate('/student/login', { replace: true })
  }

  const stats = data ? [
    ['Applications', data.stats.total_applications, FileCheck2],
    ['In review', data.stats.under_review, BriefcaseBusiness],
    ['Shortlisted', data.stats.shortlisted, UserRoundCheck],
    ['Upcoming interviews', data.stats.upcoming_interviews, CalendarClock],
    ['Selected', data.stats.selected, Award],
  ] : []

  return <main className="dashboard-shell"><DashboardNav disabled={signingOut} onSignOut={signOut} /><section className="container py-5">{loading ? <Loading /> : data && <>
    <div className="dashboard-hero mb-4"><div><p className="eyebrow mb-2">Student placement workspace</p><h1 className="display-6 fw-bold mb-2">Welcome back, {user.first_name || 'student'}</h1><p className="text-secondary mb-0">Track your placement journey and discover opportunities selected for your college.</p></div><div className="profile-progress"><strong>{data.profile_completion}%</strong><span>Profile ready</span><div><i style={{ width: `${data.profile_completion}%` }} /></div><Link to="/student/profile">Improve profile</Link></div></div>
    <div className="admin-stat-grid mb-4">{stats.map(([label, value, Icon]) => <article className="admin-stat-card" key={label}><span><Icon size={20} /></span><div><small>{label}</small><strong>{value}</strong></div></article>)}</div>
    <PortalActionGrid items={studentActions} />
    <div className="row g-4"><div className="col-12 col-xl-7"><DashboardSection action="View all" icon={Sparkles} title="Recommended for you" to="/student/opportunities">{data.recommended_opportunities.length ? <div className="dashboard-list">{data.recommended_opportunities.map((item) => <div className="dashboard-list-row" key={item.id}><span className="portfolio-icon"><Target size={18} /></span><div className="flex-grow-1 min-width-0"><strong>{item.title}</strong><small>{item.company.name} · {item.location} · {item.work_mode_display}</small><span>{item.match_reasons[0] || 'Eligible for your profile'} · Apply by {formatDate(item.application_deadline)}</span></div><span className="eligibility-badge eligible">{item.match_score}% match</span></div>)}</div> : <Empty text="No new eligible opportunities right now." />}</DashboardSection></div>
    <div className="col-12 col-xl-5"><DashboardSection action="View schedule" icon={CalendarClock} title="Upcoming interviews" to="/student/interviews">{data.upcoming_interviews.length ? <div className="dashboard-list">{data.upcoming_interviews.map((item) => <div className="dashboard-list-row" key={item.id}><span className="portfolio-icon"><CalendarClock size={18} /></span><div><strong>{item.opportunity.company.name}</strong><small>{item.recruitment_round.name} · {item.opportunity.title}</small><span>{formatDateTime(item.scheduled_at)} · {item.mode_display}</span></div></div>)}</div> : <Empty text="No interviews scheduled yet." />}</DashboardSection></div>
    <div className="col-12"><DashboardSection action="All applications" icon={FileCheck2} title="Recent applications" to="/student/applications">{data.recent_applications.length ? <div className="dashboard-list">{data.recent_applications.map((item) => <div className="dashboard-list-row" key={item.id}><span className="portfolio-icon"><BriefcaseBusiness size={18} /></span><div className="flex-grow-1"><strong>{item.opportunity.title}</strong><small>{item.opportunity.company.name} · Applied {formatDateTime(item.applied_at)}</small></div><span className={`application-status status-${item.status.toLowerCase().replace('_', '-')}`}>{item.status_display}</span></div>)}</div> : <Empty text="Apply to an opportunity to begin tracking your progress." />}</DashboardSection></div></div>
    <div className="row g-4 mt-0"><div className="col-12"><DashboardSection action="View announcements" icon={BellRing} title="Latest announcements" to="/student/announcements">{data.announcements.length ? <div className="dashboard-list">{data.announcements.map((item) => <div className="dashboard-list-row" key={item.id}><span className="portfolio-icon"><BellRing size={18} /></span><div className="flex-grow-1"><strong>{item.title}</strong><small>{item.company?.name || item.college.name} · {item.announcement_type_display}</small><span>{formatDateTime(item.publish_at)}</span></div>{!item.is_read && <span className="badge text-bg-primary">New</span>}</div>)}</div> : <Empty text="No current placement announcements." />}</DashboardSection></div></div>
  </>}</section></main>
}

const studentActions = [
  { title: 'Find opportunities', description: 'Eligible jobs and internships', icon: Target, to: '/student/opportunities' },
  { title: 'Placement readiness', description: 'Check profile and document status', icon: Sparkles, to: '/student/readiness' },
  { title: 'Applications', description: 'Track every application stage', icon: FileCheck2, to: '/student/applications' },
  { title: 'Interviews', description: 'View your interview schedule', icon: CalendarClock, to: '/student/interviews' },
  { title: 'Career portfolio', description: 'Skills, projects and experience', icon: UserRoundCheck, to: '/student/portfolio' },
  { title: 'Resumes', description: 'Upload and manage resumes', icon: BriefcaseBusiness, to: '/student/resumes' },
  { title: 'Documents', description: 'Submit documents for verification', icon: FileCheck2, to: '/student/documents' },
  { title: 'Placement drives', description: 'Explore upcoming campus drives', icon: CalendarClock, to: '/student/drives' },
  { title: 'Announcements', description: 'College and company updates', icon: BellRing, to: '/student/announcements' },
  { title: 'Placement offers', description: 'Review your final outcomes', icon: Award, to: '/student/placements' },
]

function DashboardNav({ disabled, onSignOut }) { return <nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><div className="d-flex align-items-center gap-2"><NotificationBell /><button className="btn btn-outline-secondary d-flex align-items-center gap-2" disabled={disabled} onClick={onSignOut} type="button"><LogOut size={17} /> Sign out</button></div></nav> }
function DashboardSection({ action, children, icon: Icon, title, to }) { return <section className="profile-card h-100"><div className="dashboard-section-title"><div><Icon size={19} /><h2>{title}</h2></div><Link to={to}>{action}</Link></div>{children}</section> }
function Empty({ text }) { return <div className="portfolio-empty">{text}</div> }
function Loading() { return <div className="text-center py-5"><div className="spinner-border text-primary" /></div> }
function formatDate(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`)) }
function formatDateTime(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) }

export default StudentDashboardPage
