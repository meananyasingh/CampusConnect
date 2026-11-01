import { ArrowLeft, CalendarClock, FileText, UserRound } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { placementService } from '../../services/placementService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

function CollegeOversightPage() {
  const [applications, setApplications] = useState([])
  const [interviews, setInterviews] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      placementService.listAdminApplications({ ordering: '-updated_at' }),
      placementService.listAdminInterviews({ ordering: 'scheduled_at' }),
    ]).then(([applicationItems, interviewItems]) => {
      setApplications(applicationItems)
      setInterviews(interviewItems)
    }).catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  return <main className="profile-page"><nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/admin-dashboard"><ArrowLeft size={17} /> Dashboard</Link></nav><div className="container py-5"><div className="mb-4"><p className="eyebrow mb-2">College oversight</p><h1 className="h2 fw-bold mb-2">Applications and interviews</h1><p className="text-secondary mb-0">Monitor recruitment activity involving students from your college.</p></div>{loading ? <div className="text-center py-5"><div className="spinner-border text-primary" /></div> : <div className="row g-4"><div className="col-12 col-xl-7"><section className="profile-card h-100"><h2 className="h5 fw-bold mb-3">Recent applications</h2>{applications.length ? <div className="d-grid gap-3">{applications.map((application) => <div className="oversight-row" key={application.id}><span className="portfolio-icon"><UserRound size={18} /></span><div className="flex-grow-1"><strong>{candidateName(application)}</strong><small>{application.opportunity.title} · {application.opportunity.company.name}</small><a href={application.resume.file_url} rel="noreferrer" target="_blank"><FileText size={14} /> Resume</a></div><span className={`application-status status-${application.status.toLowerCase().replace('_', '-')}`}>{application.status_display}</span></div>)}</div> : <div className="portfolio-empty">No student applications yet.</div>}</section></div><div className="col-12 col-xl-5"><section className="profile-card h-100"><h2 className="h5 fw-bold mb-3">Interview schedule</h2>{interviews.length ? <div className="d-grid gap-3">{interviews.map((interview) => <div className="oversight-row" key={interview.id}><span className="portfolio-icon"><CalendarClock size={18} /></span><div><strong>{candidateName(interview.application)}</strong><small>{interview.recruitment_round.name} · {formatDateTime(interview.scheduled_at)}</small><small>{interview.application.opportunity.company.name}</small></div></div>)}</div> : <div className="portfolio-empty">No interviews scheduled.</div>}</section></div></div>}</div></main>
}

function candidateName(application) { return `${application.student.user.first_name} ${application.student.user.last_name}`.trim() || application.student.user.email }
function formatDateTime(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) }

export default CollegeOversightPage
