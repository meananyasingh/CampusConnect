import { ArrowLeft, Building2, CheckCircle2, Clock3, MapPin, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { opportunityService } from '../../services/opportunityService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const statusFilters = [['', 'All requests'], ['PENDING', 'Awaiting review'], ['APPROVED', 'Approved'], ['REJECTED', 'Rejected'], ['WITHDRAWN', 'Withdrawn']]

function OpportunityRequestsPage() {
  const [invitations, setInvitations] = useState([])
  const [statusFilter, setStatusFilter] = useState('PENDING')
  const [search, setSearch] = useState('')
  const [notes, setNotes] = useState({})
  const [loading, setLoading] = useState(true)
  const [reviewingId, setReviewingId] = useState(null)

  const load = async (status = statusFilter, searchTerm = search) => {
    setLoading(true)
    try {
      setInvitations(await opportunityService.listCollegeInvitations({ ...(status ? { status } : {}), ...(searchTerm ? { search: searchTerm } : {}), ordering: '-submitted_at' }))
    } catch (error) { toast.error(getApiErrorMessage(error)) } finally { setLoading(false) }
  }

  useEffect(() => {
    opportunityService.listCollegeInvitations({ status: 'PENDING', ordering: '-submitted_at' })
      .then(setInvitations).catch((error) => toast.error(getApiErrorMessage(error))).finally(() => setLoading(false))
  }, [])

  const review = async (invitation, status) => {
    const reviewNote = notes[invitation.id] ?? invitation.review_note ?? ''
    if (status === 'REJECTED' && !reviewNote.trim()) { toast.error('Add a reason before rejecting this opportunity.'); return }
    setReviewingId(invitation.id)
    try {
      const updated = await opportunityService.reviewCollegeInvitation(invitation.id, { status, review_note: reviewNote })
      setInvitations((current) => statusFilter && updated.status !== statusFilter ? current.filter((item) => item.id !== updated.id) : current.map((item) => item.id === updated.id ? updated : item))
      toast.success(`Opportunity ${updated.status_display.toLowerCase()}.`)
    } catch (error) { toast.error(getApiErrorMessage(error)) } finally { setReviewingId(null) }
  }

  return <main className="profile-page"><nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/admin-dashboard"><ArrowLeft size={17} /> Dashboard</Link></nav><div className="container py-5"><div className="d-flex flex-wrap justify-content-between align-items-end gap-3 mb-4"><div><p className="eyebrow mb-2">College placement office</p><h1 className="h2 fw-bold mb-2">Opportunity requests</h1><p className="text-secondary mb-0">Review each job or internship before it becomes visible to your students.</p></div><div className="d-flex flex-wrap gap-2"><form className="d-flex gap-2" onSubmit={(event) => { event.preventDefault(); load() }}><input aria-label="Search opportunity requests" className="form-control" onChange={(event) => setSearch(event.target.value)} placeholder="Company or opportunity" value={search} /><button className="btn btn-outline-primary" type="submit">Search</button></form><select aria-label="Request status" className="form-select opportunity-review-filter" onChange={(event) => { setStatusFilter(event.target.value); load(event.target.value, search) }} value={statusFilter}>{statusFilters.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div></div>{loading ? <Loading /> : invitations.length ? <div className="d-grid gap-4">{invitations.map((invitation) => <InvitationCard invitation={invitation} key={invitation.id} note={notes[invitation.id] ?? invitation.review_note ?? ''} onNote={(value) => setNotes((current) => ({ ...current, [invitation.id]: value }))} onReview={review} reviewing={reviewingId === invitation.id} />)}</div> : <div className="profile-card portfolio-empty">No opportunity requests match this view.</div>}</div></main>
}

function InvitationCard({ invitation, note, onNote, onReview, reviewing }) {
  const item = invitation.opportunity
  return <article className="profile-card opportunity-review-card"><header><div className="d-flex gap-3"><span className="portfolio-icon"><Building2 size={20} /></span><div><p className="eyebrow mb-1">{item.company.name}</p><h2 className="h5 fw-bold mb-1">{item.title}</h2><p className="text-secondary small mb-0"><MapPin size={14} /> {item.location} · {item.work_mode_display} · Deadline {formatDate(item.application_deadline)}</p></div></div><span className={`invitation-status status-${invitation.status.toLowerCase()}`}>{invitation.status_display}</span></header><p className="text-secondary small mt-3 mb-3">{item.description}</p><div className="row g-3 small"><Detail label="Type" value={item.opportunity_type_display} /><Detail label="Openings" value={item.openings} /><Detail label="Minimum CGPA" value={item.min_cgpa} /><Detail label="Maximum backlogs" value={item.max_active_backlogs} /><Detail label="Compensation" value={formatCompensation(item)} /><Detail label="Eligible programs" value={invitation.eligible_programs.length ? invitation.eligible_programs.map((program) => program.branch).join(', ') : 'All college programs'} /></div>{item.required_skills.length > 0 && <div className="candidate-skills mt-3">{item.required_skills.map((skill) => <span key={skill}>{skill}</span>)}</div>}{invitation.recruiter_message && <div className="recruiter-request-message mt-3"><strong>Recruiter message</strong><p>{invitation.recruiter_message}</p></div>}<div className="mt-3"><label className="form-label fw-semibold small" htmlFor={`opportunity-note-${invitation.id}`}>College review note {invitation.status === 'PENDING' && '(required for rejection)'}</label><textarea className="form-control" disabled={invitation.status === 'WITHDRAWN'} id={`opportunity-note-${invitation.id}`} maxLength="1000" onChange={(event) => onNote(event.target.value)} placeholder="Provide approval guidance or explain required changes" rows="2" value={note} /></div>{invitation.status !== 'WITHDRAWN' && <div className="d-flex flex-wrap gap-2 mt-3"><button className="btn btn-success btn-sm d-flex align-items-center gap-1" disabled={reviewing} onClick={() => onReview(invitation, 'APPROVED')} type="button"><CheckCircle2 size={15} /> Approve for students</button><button className="btn btn-outline-danger btn-sm d-flex align-items-center gap-1" disabled={reviewing} onClick={() => onReview(invitation, 'REJECTED')} type="button"><XCircle size={15} /> Reject with reason</button>{invitation.reviewed_at && <span className="reviewed-time"><Clock3 size={14} /> Reviewed {formatDateTime(invitation.reviewed_at)}</span>}</div>}</article>
}

function Detail({ label, value }) { return <div className="col-6 col-lg-4"><strong>{label}</strong><br /><span className="text-secondary">{value}</span></div> }
function Loading() { return <div className="text-center py-5"><div className="spinner-border text-primary" /></div> }
function formatDate(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`)) }
function formatDateTime(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) }
function formatCompensation(item) { if (item.compensation_min == null && item.compensation_max == null) return 'Not disclosed'; const formatter = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }); return `${item.compensation_min != null ? formatter.format(Number(item.compensation_min)) : '—'} – ${item.compensation_max != null ? formatter.format(Number(item.compensation_max)) : '—'}` }

export default OpportunityRequestsPage
