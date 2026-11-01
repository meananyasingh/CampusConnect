import { ArrowLeft, FileText, Search, UserRound } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link, useSearchParams } from 'react-router-dom'

import { applicationService } from '../../services/applicationService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const transitions = {
  APPLIED: [['UNDER_REVIEW', 'Move to review'], ['SHORTLISTED', 'Shortlist'], ['REJECTED', 'Reject']],
  UNDER_REVIEW: [['SHORTLISTED', 'Shortlist'], ['REJECTED', 'Reject']],
  SHORTLISTED: [['SELECTED', 'Select'], ['REJECTED', 'Reject']],
  INTERVIEW: [['SELECTED', 'Select'], ['REJECTED', 'Reject']],
}

function RecruiterApplicationsPage() {
  const [searchParams] = useSearchParams()
  const opportunityId = searchParams.get('opportunity') || ''
  const [applications, setApplications] = useState([])
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)

  const load = async (extra = {}) => {
    setLoading(true)
    try {
      setApplications(await applicationService.listRecruiter({
        ...(opportunityId ? { opportunity: opportunityId } : {}),
        ...(search ? { search } : {}),
        ...(statusFilter ? { status: statusFilter } : {}),
        ...extra,
      }))
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    applicationService.listRecruiter(opportunityId ? { opportunity: opportunityId } : {})
      .then(setApplications)
      .catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [opportunityId])

  const updateStatus = async (application, nextStatus, note) => {
    try {
      const updated = await applicationService.updateStatus(application.id, { status: nextStatus, note })
      setApplications((current) => current.map((item) => item.id === updated.id ? updated : item))
      toast.success(`Application marked as ${updated.status_display.toLowerCase()}.`)
    } catch (error) {
      toast.error(getApiErrorMessage(error))
      throw error
    }
  }

  return (
    <main className="profile-page">
      <nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/recruiter/dashboard"><ArrowLeft size={17} /> Dashboard</Link></nav>
      <div className="container py-5"><div className="mb-4"><p className="eyebrow mb-2">Recruitment pipeline</p><h1 className="h2 fw-bold mb-2">Applicants</h1><p className="text-secondary mb-0">Review candidates and move them through controlled recruitment stages.</p></div><form className="profile-card mb-4" onSubmit={(event) => { event.preventDefault(); load() }}><div className="row g-3 align-items-end"><div className="col-12 col-md-8"><label className="form-label fw-semibold" htmlFor="applicant-search">Search candidates</label><div className="input-group"><span className="input-group-text"><Search size={17} /></span><input className="form-control" id="applicant-search" onChange={(event) => setSearch(event.target.value)} placeholder="Name, email, enrollment number, or opportunity" value={search} /></div></div><div className="col-12 col-md-4"><label className="form-label fw-semibold" htmlFor="application-status">Status</label><select className="form-select" id="application-status" onChange={(event) => setStatusFilter(event.target.value)} value={statusFilter}><option value="">All statuses</option><option value="APPLIED">Applied</option><option value="UNDER_REVIEW">Under review</option><option value="SHORTLISTED">Shortlisted</option><option value="INTERVIEW">Interview stage</option><option value="SELECTED">Selected</option><option value="REJECTED">Rejected</option><option value="WITHDRAWN">Withdrawn</option></select></div><div className="col-12 text-end"><button className="btn btn-primary" type="submit">Apply filters</button></div></div></form>{loading ? <div className="text-center py-5"><div className="spinner-border text-primary" /></div> : applications.length ? <div className="d-grid gap-4">{applications.map((application) => <ApplicantCard application={application} key={application.id} onUpdate={updateStatus} />)}</div> : <div className="profile-card portfolio-empty">No applicants match the current filters.</div>}</div>
    </main>
  )
}

function ApplicantCard({ application, onUpdate }) {
  const [nextStatus, setNextStatus] = useState('')
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)
  const studentName = `${application.student.user.first_name} ${application.student.user.last_name}`.trim() || application.student.user.email
  const submit = async (event) => {
    event.preventDefault()
    if (!nextStatus) return
    setSaving(true)
    try {
      await onUpdate(application, nextStatus, note)
      setNextStatus('')
      setNote('')
    } finally {
      setSaving(false)
    }
  }
  return <article className="profile-card"><div className="d-flex flex-wrap justify-content-between gap-3"><div className="d-flex gap-3"><span className="portfolio-icon"><UserRound size={20} /></span><div><p className="text-secondary small mb-1">{application.opportunity.title}</p><h2 className="h5 fw-bold mb-1">{studentName}</h2><p className="text-secondary small mb-0">{application.student.enrollment_number} · {application.student.program_name}</p></div></div><span className={`application-status status-${application.status.toLowerCase().replace('_', '-')}`}>{application.status_display}</span></div><div className="row g-3 mt-1 small"><div className="col-md-4"><strong>Email</strong><br />{application.student.user.email}</div><div className="col-md-3"><strong>CGPA</strong><br />{application.student.cgpa ?? 'Not provided'}</div><div className="col-md-5"><strong>Submitted resume</strong><br /><a className="d-inline-flex align-items-center gap-1" href={application.resume.file_url} rel="noreferrer" target="_blank"><FileText size={15} /> {application.resume.title}</a></div></div>{application.cover_letter && <p className="application-cover-letter mt-3 mb-0">{application.cover_letter}</p>}{application.status === 'SHORTLISTED' && <div className="mt-3"><Link className="btn btn-sm btn-outline-primary" to={`/recruiter/opportunities/${application.opportunity.id}/process`}>Schedule interview</Link></div>}{transitions[application.status]?.length > 0 && <form className="row g-2 align-items-end mt-3" onSubmit={submit}><div className="col-12 col-md-4"><label className="form-label small fw-semibold" htmlFor={`status-${application.id}`}>Next stage</label><select className="form-select" id={`status-${application.id}`} onChange={(event) => setNextStatus(event.target.value)} required value={nextStatus}><option value="">Select action</option>{transitions[application.status].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div><div className="col-12 col-md-6"><label className="form-label small fw-semibold" htmlFor={`note-${application.id}`}>Status note visible to student (optional)</label><input className="form-control" id={`note-${application.id}`} maxLength="500" onChange={(event) => setNote(event.target.value)} value={note} /></div><div className="col-12 col-md-2"><button className="btn btn-primary w-100" disabled={saving} type="submit">{saving ? 'Saving…' : 'Update'}</button></div></form>}</article>
}

export default RecruiterApplicationsPage
