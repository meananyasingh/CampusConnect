import { ArrowLeft, Building2, CalendarClock, ExternalLink, MapPin, Video } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { applicationService } from '../../services/applicationService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

function StudentInterviewsPage() {
  const [interviews, setInterviews] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    applicationService.listStudentInterviews({ ordering: 'scheduled_at' })
      .then(setInterviews)
      .catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  return (
    <main className="profile-page">
      <nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/student/dashboard"><ArrowLeft size={17} /> Dashboard</Link></nav>
      <div className="container py-5"><div className="mb-4"><p className="eyebrow mb-2">Recruitment schedule</p><h1 className="h2 fw-bold mb-2">My interviews</h1><p className="text-secondary mb-0">Find interview timings, joining details, instructions and published results.</p></div>{loading ? <div className="text-center py-5"><div className="spinner-border text-primary" /></div> : interviews.length ? <div className="row g-4">{interviews.map((interview) => <InterviewCard interview={interview} key={interview.id} />)}</div> : <div className="profile-card portfolio-empty">No interviews have been scheduled yet.</div>}</div>
    </main>
  )
}

function InterviewCard({ interview }) {
  const location = interview.mode === 'ONLINE' ? interview.meeting_link : interview.venue
  return <div className="col-12 col-lg-6"><article className="profile-card h-100"><div className="d-flex justify-content-between gap-3"><div className="d-flex gap-3"><span className="portfolio-icon"><CalendarClock size={20} /></span><div><p className="text-secondary small mb-1">{interview.opportunity.company.name} · {interview.opportunity.title}</p><h2 className="h5 fw-bold mb-1">Round {interview.recruitment_round.sequence}: {interview.recruitment_round.name}</h2><p className="text-secondary small mb-0">{interview.recruitment_round.round_type_display}</p></div></div><span className={`application-status status-${interview.status.toLowerCase()}`}>{interview.status_display}</span></div><div className="interview-details mt-4"><div><CalendarClock size={17} /><span><strong>{formatDateTime(interview.scheduled_at)}</strong>{interview.duration_minutes} minutes</span></div><div>{interview.mode === 'ONLINE' ? <Video size={17} /> : <Building2 size={17} />}<span><strong>{interview.mode_display}</strong>{interview.mode === 'PHONE' ? 'Recruiter will contact you' : location || 'Details pending'}</span></div>{interview.mode === 'ONSITE' && interview.venue && <div><MapPin size={17} /><span><strong>Venue</strong>{interview.venue}</span></div>}</div>{interview.mode === 'ONLINE' && interview.meeting_link && interview.status === 'SCHEDULED' && <a className="btn btn-outline-primary btn-sm d-inline-flex align-items-center gap-2 mt-3" href={interview.meeting_link} rel="noreferrer" target="_blank">Join meeting <ExternalLink size={15} /></a>}{interview.instructions && <div className="application-cover-letter mt-3"><strong>Instructions</strong><br />{interview.instructions}</div>}{interview.result !== 'PENDING' && <div className={`alert ${interview.result === 'PASSED' ? 'alert-success' : 'alert-secondary'} small mt-3 mb-0`}>Result: <strong>{interview.result_display}</strong></div>}</article></div>
}

function formatDateTime(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'full', timeStyle: 'short' }).format(new Date(value)) }

export default StudentInterviewsPage
