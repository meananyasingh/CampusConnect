import { ArrowLeft, BriefcaseBusiness, Clock3, FileText } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { useConfirmDialog } from '../../hooks/useConfirmDialog.js'
import { applicationService } from '../../services/applicationService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const withdrawable = new Set(['APPLIED', 'UNDER_REVIEW', 'SHORTLISTED'])

function StudentApplicationsPage() {
  const confirmAction = useConfirmDialog()
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const [withdrawingId, setWithdrawingId] = useState(null)

  useEffect(() => {
    applicationService.listStudent()
      .then(setApplications)
      .catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  const withdraw = async (application) => {
    if (!await confirmAction({ title: 'Withdraw application?', message: `Your application for “${application.opportunity.title}” will be withdrawn.`, confirmLabel: 'Withdraw application' })) return
    setWithdrawingId(application.id)
    try {
      const updated = await applicationService.withdraw(application.id)
      setApplications((current) => current.map((item) => item.id === updated.id ? updated : item))
      toast.success('Application withdrawn.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setWithdrawingId(null)
    }
  }

  return (
    <main className="profile-page">
      <nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/student/dashboard"><ArrowLeft size={17} /> Dashboard</Link></nav>
      <div className="container py-5">
        <div className="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4"><div><p className="eyebrow mb-2">Application tracker</p><h1 className="h2 fw-bold mb-2">My applications</h1><p className="text-secondary mb-0">Track every stage and the resume submitted for each opportunity.</p></div><div className="d-flex gap-2"><Link className="btn btn-outline-primary" to="/student/interviews">My interviews</Link><Link className="btn btn-primary" to="/student/opportunities">Browse opportunities</Link></div></div>
        {loading ? <div className="text-center py-5"><div className="spinner-border text-primary" /></div> : applications.length ? <div className="d-grid gap-4">{applications.map((application) => <ApplicationCard application={application} key={application.id} onWithdraw={() => withdraw(application)} withdrawing={withdrawingId === application.id} />)}</div> : <div className="profile-card portfolio-empty">You have not submitted any applications yet.</div>}
      </div>
    </main>
  )
}

function ApplicationCard({ application, onWithdraw, withdrawing }) {
  return <article className="profile-card"><div className="d-flex flex-wrap justify-content-between gap-3"><div className="d-flex gap-3"><span className="portfolio-icon"><BriefcaseBusiness size={20} /></span><div><p className="text-secondary small mb-1">{application.opportunity.company.name}</p><h2 className="h5 fw-bold mb-1">{application.opportunity.title}</h2><p className="text-secondary small mb-0">Applied {formatDateTime(application.applied_at)}</p></div></div><span className={`application-status status-${application.status.toLowerCase().replace('_', '-')}`}>{application.status_display}</span></div><div className="d-flex flex-wrap gap-3 mt-3 small"><a className="d-inline-flex align-items-center gap-1" href={application.resume.file_url} rel="noreferrer" target="_blank"><FileText size={16} /> {application.resume.title}</a><span>{application.opportunity.location} · {application.opportunity.work_mode_display}</span></div>{application.cover_letter && <p className="application-cover-letter mt-3 mb-0">{application.cover_letter}</p>}<div className="application-timeline mt-4">{application.status_history.map((history) => <div className="application-timeline-item" key={history.id}><Clock3 size={16} /><div><strong>{history.to_status_display}</strong><span>{formatDateTime(history.created_at)}</span>{history.note && <p>{history.note}</p>}</div></div>)}</div>{withdrawable.has(application.status) && <div className="text-end mt-3"><button className="btn btn-sm btn-outline-danger" disabled={withdrawing} onClick={onWithdraw} type="button">{withdrawing ? 'Withdrawing…' : 'Withdraw application'}</button></div>}</article>
}

function formatDateTime(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) }

export default StudentApplicationsPage
