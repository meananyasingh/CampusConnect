import { ArrowLeft, CalendarPlus, Plus, Video } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { Link, useParams } from 'react-router-dom'

import { useConfirmDialog } from '../../hooks/useConfirmDialog.js'
import { applicationService } from '../../services/applicationService.js'
import { opportunityService } from '../../services/opportunityService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const blankRound = { name: '', round_type: 'TECHNICAL', sequence: '1', description: '' }
const blankInterview = { recruitment_round_id: '', application_id: '', scheduled_at: '', duration_minutes: '45', mode: 'ONLINE', venue: '', meeting_link: '', instructions: '' }

function RecruitmentProcessPage() {
  const { opportunityId } = useParams()
  const [opportunity, setOpportunity] = useState(null)
  const [rounds, setRounds] = useState([])
  const [applications, setApplications] = useState([])
  const [interviews, setInterviews] = useState([])
  const [roundForm, setRoundForm] = useState(blankRound)
  const [interviewForm, setInterviewForm] = useState(blankInterview)
  const [showRoundForm, setShowRoundForm] = useState(false)
  const [showInterviewForm, setShowInterviewForm] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const candidates = useMemo(
    () => applications.filter((application) => ['SHORTLISTED', 'INTERVIEW'].includes(application.status)),
    [applications],
  )

  useEffect(() => {
    Promise.all([
      opportunityService.getRecruiter(opportunityId),
      applicationService.listRounds({ opportunity: opportunityId }),
      applicationService.listRecruiter({ opportunity: opportunityId }),
      applicationService.listRecruiterInterviews({ application__opportunity: opportunityId, ordering: 'scheduled_at' }),
    ]).then(([opportunityData, roundItems, applicationItems, interviewItems]) => {
      setOpportunity(opportunityData)
      setRounds(roundItems)
      setApplications(applicationItems)
      setInterviews(interviewItems)
      const nextSequence = roundItems.reduce((maximum, round) => Math.max(maximum, round.sequence), 0) + 1
      setRoundForm((current) => ({ ...current, sequence: String(nextSequence) }))
    }).catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [opportunityId])

  const createRound = async (event) => {
    event.preventDefault()
    setSaving(true)
    try {
      const created = await applicationService.createRound({ ...roundForm, opportunity_id: opportunityId })
      setRounds((current) => [...current, created].sort((a, b) => a.sequence - b.sequence))
      setRoundForm({ ...blankRound, sequence: String(created.sequence + 1) })
      setShowRoundForm(false)
      toast.success('Recruitment round created.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  const scheduleInterview = async (event) => {
    event.preventDefault()
    setSaving(true)
    try {
      const created = await applicationService.scheduleInterview({
        ...interviewForm,
        scheduled_at: new Date(interviewForm.scheduled_at).toISOString(),
        venue: interviewForm.mode === 'ONSITE' ? interviewForm.venue : '',
        meeting_link: interviewForm.mode === 'ONLINE' ? interviewForm.meeting_link : '',
      })
      setInterviews((current) => [...current, created].sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at)))
      setApplications((current) => current.map((application) => application.id === created.application.id ? created.application : application))
      setInterviewForm(blankInterview)
      setShowInterviewForm(false)
      toast.success('Interview scheduled and candidate notified in their portal.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  const updateInterview = async (interview, values) => {
    try {
      const updated = await applicationService.updateInterview(interview.id, values)
      setInterviews((current) => current.map((item) => item.id === updated.id ? updated : item))
      toast.success(`Interview marked as ${updated.status_display.toLowerCase()}.`)
    } catch (error) {
      toast.error(getApiErrorMessage(error))
      throw error
    }
  }

  if (loading) return <main className="profile-page"><div className="text-center py-5"><div className="spinner-border text-primary" /></div></main>

  return (
    <main className="profile-page"><nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/recruiter/opportunities"><ArrowLeft size={17} /> Opportunities</Link></nav><div className="container py-5"><div className="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4"><div><p className="eyebrow mb-2">Recruitment process</p><h1 className="h2 fw-bold mb-2">{opportunity?.title}</h1><p className="text-secondary mb-0">Configure rounds and schedule shortlisted candidates.</p></div><Link className="btn btn-outline-primary" to={`/recruiter/applications?opportunity=${opportunityId}`}>View all applicants</Link></div><section className="profile-card mb-4"><div className="d-flex justify-content-between align-items-center gap-3 mb-3"><div><h2 className="h5 fw-bold mb-1">Recruitment rounds</h2><p className="text-secondary small mb-0">Rounds run in sequence for this opportunity.</p></div><button className="btn btn-sm btn-primary d-flex align-items-center gap-2" onClick={() => setShowRoundForm((current) => !current)} type="button"><Plus size={16} /> Add round</button></div>{showRoundForm && <RoundForm form={roundForm} onChange={setRoundForm} onSubmit={createRound} saving={saving} />}{rounds.length ? <div className="round-grid">{rounds.map((round) => <div className="round-card" key={round.id}><span>{round.sequence}</span><div><strong>{round.name}</strong><small>{round.round_type_display}</small>{round.description && <p>{round.description}</p>}</div></div>)}</div> : <div className="portfolio-empty">No recruitment rounds configured yet.</div>}</section><section className="profile-card mb-4"><div className="d-flex justify-content-between align-items-center gap-3 mb-3"><div><h2 className="h5 fw-bold mb-1">Schedule candidate</h2><p className="text-secondary small mb-0">Only shortlisted candidates can be scheduled.</p></div><button className="btn btn-sm btn-primary d-flex align-items-center gap-2" disabled={!rounds.length || !candidates.length} onClick={() => setShowInterviewForm((current) => !current)} type="button"><CalendarPlus size={16} /> Schedule interview</button></div>{!rounds.length && <div className="alert alert-warning small mb-0">Create at least one round first.</div>}{rounds.length > 0 && !candidates.length && <div className="alert alert-info small mb-0">Shortlist candidates from the applicants page before scheduling them.</div>}{showInterviewForm && <InterviewForm candidates={candidates} form={interviewForm} onChange={setInterviewForm} onSubmit={scheduleInterview} rounds={rounds} saving={saving} />}</section><section className="profile-card"><h2 className="h5 fw-bold mb-3">Scheduled interviews</h2>{interviews.length ? <div className="d-grid gap-3">{interviews.map((interview) => <RecruiterInterviewCard interview={interview} key={interview.id} onUpdate={updateInterview} />)}</div> : <div className="portfolio-empty">No candidate interviews scheduled yet.</div>}</section></div></main>
  )
}

function RoundForm({ form, onChange, onSubmit, saving }) {
  const update = (event) => onChange((current) => ({ ...current, [event.target.name]: event.target.value }))
  return <form className="border rounded-3 p-3 mb-4" onSubmit={onSubmit}><div className="row g-3"><div className="col-md-5"><label className="form-label fw-semibold" htmlFor="round-name">Round name</label><input className="form-control" id="round-name" name="name" onChange={update} required value={form.name} /></div><div className="col-md-4"><label className="form-label fw-semibold" htmlFor="round-type">Type</label><select className="form-select" id="round-type" name="round_type" onChange={update} value={form.round_type}><option value="SCREENING">Screening</option><option value="APTITUDE">Aptitude test</option><option value="GROUP_DISCUSSION">Group discussion</option><option value="TECHNICAL">Technical interview</option><option value="HR">HR interview</option><option value="OTHER">Other</option></select></div><div className="col-md-3"><label className="form-label fw-semibold" htmlFor="round-sequence">Sequence</label><input className="form-control" id="round-sequence" min="1" name="sequence" onChange={update} required type="number" value={form.sequence} /></div><div className="col-12"><label className="form-label fw-semibold" htmlFor="round-description">Description</label><textarea className="form-control" id="round-description" maxLength="1500" name="description" onChange={update} rows="2" value={form.description} /></div><div className="col-12 text-end"><button className="btn btn-primary" disabled={saving} type="submit">{saving ? 'Saving…' : 'Create round'}</button></div></div></form>
}

function InterviewForm({ candidates, form, onChange, onSubmit, rounds, saving }) {
  const update = (event) => onChange((current) => ({ ...current, [event.target.name]: event.target.value }))
  return <form className="border rounded-3 p-3 mt-3" onSubmit={onSubmit}><div className="row g-3"><div className="col-md-6"><label className="form-label fw-semibold" htmlFor="schedule-round">Round</label><select className="form-select" id="schedule-round" name="recruitment_round_id" onChange={update} required value={form.recruitment_round_id}><option value="">Select round</option>{rounds.map((round) => <option key={round.id} value={round.id}>Round {round.sequence}: {round.name}</option>)}</select></div><div className="col-md-6"><label className="form-label fw-semibold" htmlFor="schedule-candidate">Candidate</label><select className="form-select" id="schedule-candidate" name="application_id" onChange={update} required value={form.application_id}><option value="">Select shortlisted candidate</option>{candidates.map((application) => <option key={application.id} value={application.id}>{candidateName(application)} — {application.student.enrollment_number}</option>)}</select></div><div className="col-md-6"><label className="form-label fw-semibold" htmlFor="scheduled-at">Date and time</label><input className="form-control" id="scheduled-at" name="scheduled_at" onChange={update} required type="datetime-local" value={form.scheduled_at} /></div><div className="col-md-3"><label className="form-label fw-semibold" htmlFor="duration">Duration (minutes)</label><input className="form-control" id="duration" max="480" min="10" name="duration_minutes" onChange={update} required type="number" value={form.duration_minutes} /></div><div className="col-md-3"><label className="form-label fw-semibold" htmlFor="interview-mode">Mode</label><select className="form-select" id="interview-mode" name="mode" onChange={update} value={form.mode}><option value="ONLINE">Online</option><option value="ONSITE">On-site</option><option value="PHONE">Phone</option></select></div>{form.mode === 'ONLINE' && <div className="col-12"><label className="form-label fw-semibold" htmlFor="meeting-link">Meeting link</label><input className="form-control" id="meeting-link" name="meeting_link" onChange={update} required type="url" value={form.meeting_link} /></div>}{form.mode === 'ONSITE' && <div className="col-12"><label className="form-label fw-semibold" htmlFor="venue">Venue</label><input className="form-control" id="venue" name="venue" onChange={update} required value={form.venue} /></div>}<div className="col-12"><label className="form-label fw-semibold" htmlFor="instructions">Candidate instructions</label><textarea className="form-control" id="instructions" maxLength="1500" name="instructions" onChange={update} rows="3" value={form.instructions} /></div><div className="col-12 text-end"><button className="btn btn-primary" disabled={saving} type="submit">{saving ? 'Scheduling…' : 'Schedule candidate'}</button></div></div></form>
}

function RecruiterInterviewCard({ interview, onUpdate }) {
  const confirmAction = useConfirmDialog()
  const [result, setResult] = useState('PASSED')
  const [feedback, setFeedback] = useState('')
  const [rating, setRating] = useState('')
  const [saving, setSaving] = useState(false)
  const complete = async (event) => { event.preventDefault(); setSaving(true); try { await onUpdate(interview, { status: 'COMPLETED', result, feedback, rating: rating || null }) } finally { setSaving(false) } }
  const cancel = async () => { if (!await confirmAction({ title: 'Cancel this interview?', message: 'The interview schedule will be cancelled and the candidate will see the updated status.', confirmLabel: 'Cancel interview' })) return; setSaving(true); try { await onUpdate(interview, { status: 'CANCELLED' }) } finally { setSaving(false) } }
  return <article className="opportunity-card"><div className="d-flex flex-wrap justify-content-between gap-3"><div><p className="text-secondary small mb-1">Round {interview.recruitment_round.sequence}: {interview.recruitment_round.name}</p><h3 className="h5 fw-bold mb-1">{candidateName(interview.application)}</h3><p className="text-secondary small mb-0">{formatDateTime(interview.scheduled_at)} · {interview.duration_minutes} min · {interview.mode_display}</p></div><div className="d-flex gap-2"><span className={`application-status status-${interview.status.toLowerCase()}`}>{interview.status_display}</span>{interview.result !== 'PENDING' && <span className="application-status">{interview.result_display}</span>}</div></div>{interview.mode === 'ONLINE' && <p className="small mt-2 mb-0"><Video size={15} /> <a href={interview.meeting_link} rel="noreferrer" target="_blank">Open meeting link</a></p>}{interview.mode === 'ONSITE' && <p className="small mt-2 mb-0">Venue: {interview.venue}</p>}{interview.status === 'SCHEDULED' && <form className="row g-2 align-items-end mt-3" onSubmit={complete}><div className="col-md-3"><label className="form-label small fw-semibold" htmlFor={`result-${interview.id}`}>Result</label><select className="form-select" id={`result-${interview.id}`} onChange={(event) => setResult(event.target.value)} value={result}><option value="PASSED">Passed</option><option value="FAILED">Not selected</option><option value="NO_SHOW">No show</option></select></div><div className="col-md-5"><label className="form-label small fw-semibold" htmlFor={`feedback-${interview.id}`}>Private feedback</label><input className="form-control" id={`feedback-${interview.id}`} maxLength="2000" onChange={(event) => setFeedback(event.target.value)} value={feedback} /></div><div className="col-md-2"><label className="form-label small fw-semibold" htmlFor={`rating-${interview.id}`}>Rating</label><select className="form-select" id={`rating-${interview.id}`} onChange={(event) => setRating(event.target.value)} value={rating}><option value="">—</option>{[1, 2, 3, 4, 5].map((value) => <option key={value} value={value}>{value}/5</option>)}</select></div><div className="col-md-2 d-grid gap-1"><button className="btn btn-sm btn-success" disabled={saving} type="submit">Complete</button><button className="btn btn-sm btn-outline-danger" disabled={saving} onClick={cancel} type="button">Cancel</button></div></form>}{interview.feedback && <p className="application-cover-letter mt-3 mb-0"><strong>Private feedback:</strong> {interview.feedback}{interview.rating && ` · ${interview.rating}/5`}</p>}</article>
}

function candidateName(application) { return `${application.student.user.first_name} ${application.student.user.last_name}`.trim() || application.student.user.email }
function formatDateTime(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) }

export default RecruitmentProcessPage
