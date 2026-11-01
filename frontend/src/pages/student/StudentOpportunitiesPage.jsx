import { ArrowLeft, Bookmark, BriefcaseBusiness, CheckCircle2, MapPin, Search, Send, Sparkles, X, XCircle } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { applicationService } from '../../services/applicationService.js'
import { opportunityService } from '../../services/opportunityService.js'
import { placementService } from '../../services/placementService.js'
import { studentService } from '../../services/studentService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

function StudentOpportunitiesPage() {
  const [opportunities, setOpportunities] = useState([])
  const [applications, setApplications] = useState([])
  const [resumes, setResumes] = useState([])
  const [readiness, setReadiness] = useState(null)
  const [filters, setFilters] = useState({ search: '', opportunity_type: '', work_mode: '', company: '', skill: '', min_compensation: '', deadline_before: '', eligible_only: '', ordering: '-published_at' })
  const [viewMode, setViewMode] = useState('all')
  const [applyItem, setApplyItem] = useState(null)
  const [resumeId, setResumeId] = useState('')
  const [coverLetter, setCoverLetter] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const applicationsByOpportunity = useMemo(
    () => new Map(applications.map((application) => [application.opportunity.id, application])),
    [applications],
  )

  const load = async (params = filters) => {
    setLoading(true)
    try {
      setOpportunities(await opportunityService.listStudent(
        Object.fromEntries(Object.entries(params).filter(([, value]) => value)),
      ))
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  const selectView = async (mode) => {
    setViewMode(mode)
    setLoading(true)
    try {
      const items = mode === 'recommended'
        ? await opportunityService.listRecommended()
        : await opportunityService.listStudent(mode === 'saved' ? { saved_only: true, ordering: '-published_at' } : {})
      setOpportunities(items)
    } catch (error) { toast.error(getApiErrorMessage(error)) } finally { setLoading(false) }
  }

  const toggleSaved = async (item) => {
    try {
      await (item.is_saved ? opportunityService.unsave(item.id) : opportunityService.save(item.id))
      if (viewMode === 'saved') setOpportunities((current) => current.filter((entry) => entry.id !== item.id))
      else setOpportunities((current) => current.map((entry) => entry.id === item.id ? { ...entry, is_saved: !item.is_saved } : entry))
      toast.success(item.is_saved ? 'Removed from saved opportunities.' : 'Opportunity saved.')
    } catch (error) { toast.error(getApiErrorMessage(error)) }
  }

  useEffect(() => {
    Promise.all([
      opportunityService.listStudent(),
      applicationService.listStudent(),
      studentService.getResumes(),
      placementService.getStudentReadiness(),
    ]).then(([opportunityItems, applicationItems, resumeItems, readinessData]) => {
      setOpportunities(opportunityItems)
      setApplications(applicationItems)
      setResumes(resumeItems)
      setReadiness(readinessData)
    }).catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  const openApplication = (opportunity) => {
    if (!resumes.length) {
      toast.error('Upload a PDF resume before applying.')
      return
    }
    setApplyItem(opportunity)
    setResumeId(String(resumes.find((resume) => resume.is_primary)?.id || resumes[0].id))
    setCoverLetter('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const submitApplication = async (event) => {
    event.preventDefault()
    setSubmitting(true)
    try {
      const application = await applicationService.apply({
        opportunity_id: applyItem.id,
        resume_id: resumeId,
        cover_letter: coverLetter,
      })
      setApplications((current) => [application, ...current])
      setApplyItem(null)
      toast.success('Application submitted successfully.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="profile-page">
      <nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><div className="d-flex gap-2"><Link className="btn btn-outline-primary" to="/student/applications">My applications</Link><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/student/dashboard"><ArrowLeft size={17} /> Dashboard</Link></div></nav>
      <div className="container py-5">
        <div className="d-flex flex-wrap justify-content-between align-items-end gap-3 mb-4"><div><p className="eyebrow mb-2">Career opportunities</p><h1 className="h2 fw-bold mb-2">Jobs and internships</h1><p className="text-secondary mb-0">Search, save, and apply to active opportunities shared with your college.</p></div><div className="opportunity-view-tabs"><button className={viewMode === 'all' ? 'active' : ''} onClick={() => selectView('all')} type="button">All</button><button className={viewMode === 'recommended' ? 'active' : ''} onClick={() => selectView('recommended')} type="button"><Sparkles size={14} /> Recommended</button><button className={viewMode === 'saved' ? 'active' : ''} onClick={() => selectView('saved')} type="button"><Bookmark size={14} /> Saved</button></div></div>
        {readiness && !readiness.is_ready && <div className="alert alert-warning d-flex flex-wrap justify-content-between align-items-center gap-3"><span>Your college placement requirements are incomplete. You can browse opportunities, but cannot apply yet.</span><Link className="alert-link" to="/student/readiness">View readiness</Link></div>}
        {applyItem && <ApplicationEditor coverLetter={coverLetter} item={applyItem} onCancel={() => setApplyItem(null)} onCoverLetterChange={setCoverLetter} onResumeChange={setResumeId} onSubmit={submitApplication} resumeId={resumeId} resumes={resumes} submitting={submitting} />}
        {viewMode === 'all' && <form className="profile-card mb-4" onSubmit={(event) => { event.preventDefault(); setViewMode('all'); load(filters) }}><div className="row g-3 align-items-end"><div className="col-12 col-lg-6"><label className="form-label fw-semibold" htmlFor="opportunity-search">Search</label><div className="input-group"><span className="input-group-text"><Search size={17} /></span><input className="form-control" id="opportunity-search" onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))} placeholder="Role, company, location, or skill" value={filters.search} /></div></div><FilterSelect label="Type" name="opportunity_type" onChange={setFilters} options={[["", "All types"], ["JOB", "Jobs"], ["INTERNSHIP", "Internships"]]} value={filters.opportunity_type} /><FilterSelect label="Work mode" name="work_mode" onChange={setFilters} options={[["", "All modes"], ["ONSITE", "On-site"], ["REMOTE", "Remote"], ["HYBRID", "Hybrid"]]} value={filters.work_mode} /><FilterInput label="Company" name="company" onChange={setFilters} placeholder="Company name" value={filters.company} /><FilterInput label="Required skill" name="skill" onChange={setFilters} placeholder="Django" value={filters.skill} /><FilterInput label="Minimum compensation" min="0" name="min_compensation" onChange={setFilters} type="number" value={filters.min_compensation} /><FilterInput label="Deadline before" name="deadline_before" onChange={setFilters} type="date" value={filters.deadline_before} /><FilterSelect label="Eligibility" name="eligible_only" onChange={setFilters} options={[["", "All results"], ["true", "Eligible only"]]} value={filters.eligible_only} /><FilterSelect label="Sort by" name="ordering" onChange={setFilters} options={[["-published_at", "Newest"], ["application_deadline", "Deadline soon"], ["-compensation_max", "Highest compensation"]]} value={filters.ordering} /><div className="col-12 d-flex justify-content-end gap-2"><button className="btn btn-outline-secondary" onClick={() => { const reset = { search: '', opportunity_type: '', work_mode: '', company: '', skill: '', min_compensation: '', deadline_before: '', eligible_only: '', ordering: '-published_at' }; setFilters(reset); load(reset) }} type="button">Clear</button><button className="btn btn-primary" type="submit">Apply filters</button></div></div></form>}
        {loading ? <div className="text-center py-5"><div className="spinner-border text-primary" /></div> : opportunities.length ? <div className="row g-4">{opportunities.map((item) => <StudentOpportunityCard application={applicationsByOpportunity.get(item.id)} item={item} key={item.id} onApply={() => openApplication(item)} onToggleSaved={() => toggleSaved(item)} />)}</div> : <div className="profile-card portfolio-empty">{viewMode === 'saved' ? 'You have not saved any active opportunities.' : viewMode === 'recommended' ? 'Complete your preferences and skills to improve recommendations.' : 'No matching opportunities are currently available for your college.'}</div>}
      </div>
    </main>
  )
}

function ApplicationEditor({ coverLetter, item, onCancel, onCoverLetterChange, onResumeChange, onSubmit, resumeId, resumes, submitting }) {
  return <section className="profile-card mb-4"><div className="d-flex justify-content-between gap-3 mb-3"><div><p className="eyebrow mb-1">Submit application</p><h2 className="h5 fw-bold mb-0">{item.title} at {item.company.name}</h2></div><button aria-label="Close application form" className="btn btn-sm btn-light" onClick={onCancel} type="button"><X size={17} /></button></div><form onSubmit={onSubmit}><div className="mb-3"><label className="form-label fw-semibold" htmlFor="application-resume">Resume</label><select className="form-select" id="application-resume" onChange={(event) => onResumeChange(event.target.value)} required value={resumeId}>{resumes.map((resume) => <option key={resume.id} value={resume.id}>{resume.title}{resume.is_primary ? ' (Primary)' : ''}</option>)}</select><small className="text-secondary">This resume version will remain attached to the application.</small></div><div><label className="form-label fw-semibold" htmlFor="cover-letter">Cover letter (optional)</label><textarea className="form-control" id="cover-letter" maxLength="3000" onChange={(event) => onCoverLetterChange(event.target.value)} placeholder="Briefly explain why you are a good fit." rows="5" value={coverLetter} /></div><div className="d-flex justify-content-end gap-2 mt-4"><button className="btn btn-outline-secondary" onClick={onCancel} type="button">Cancel</button><button className="btn btn-primary d-flex align-items-center gap-2" disabled={submitting} type="submit"><Send size={17} /> {submitting ? 'Submitting…' : 'Submit application'}</button></div></form></section>
}

function FilterSelect({ label, name, onChange, options, value }) {
  return <div className="col-6 col-lg-3"><label className="form-label fw-semibold" htmlFor={name}>{label}</label><select className="form-select" id={name} onChange={(event) => onChange((current) => ({ ...current, [name]: event.target.value }))} value={value}>{options.map(([key, text]) => <option key={key} value={key}>{text}</option>)}</select></div>
}

function FilterInput({ label, name, onChange, type = 'text', value, ...props }) {
  return <div className="col-6 col-lg-3"><label className="form-label fw-semibold" htmlFor={name}>{label}</label><input className="form-control" id={name} onChange={(event) => onChange((current) => ({ ...current, [name]: event.target.value }))} type={type} value={value} {...props} /></div>
}

function StudentOpportunityCard({ application, item, onApply, onToggleSaved }) {
  return <div className="col-12 col-lg-6"><article className="profile-card h-100 opportunity-student-card"><div className="d-flex justify-content-between gap-3"><div className="d-flex gap-3"><span className="portfolio-icon"><BriefcaseBusiness size={20} /></span><div><p className="text-secondary small mb-1">{item.company.name} · Campus hiring</p><h2 className="h5 fw-bold mb-1">{item.title}</h2><p className="text-secondary small mb-0"><MapPin size={14} /> {item.location} · {item.work_mode_display}</p></div></div><div className="d-flex align-items-start gap-2"><button aria-label={item.is_saved ? 'Remove saved opportunity' : 'Save opportunity'} className={`save-opportunity ${item.is_saved ? 'saved' : ''}`} onClick={onToggleSaved} type="button"><Bookmark fill={item.is_saved ? 'currentColor' : 'none'} size={17} /></button><span className={`eligibility-badge ${item.is_eligible ? 'eligible' : 'ineligible'}`}>{item.is_eligible ? <CheckCircle2 size={15} /> : <XCircle size={15} />}{item.is_eligible ? 'Eligible' : 'Not eligible'}</span></div></div>{item.match_score != null && <div className="match-summary"><strong>{item.match_score}% match</strong><span>{item.match_reasons.join(' · ')}</span></div>}<p className="small portfolio-description my-3">{item.description}</p><div className="opportunity-facts"><span><strong>{item.openings}</strong> opening{item.openings === 1 ? '' : 's'}</span><span><strong>{item.min_cgpa}</strong> min CGPA</span><span><strong>{formatDate(item.application_deadline)}</strong> deadline</span></div>{item.required_skills.length > 0 && <div className="d-flex flex-wrap gap-2 mt-3">{item.required_skills.map((skill) => <span className={`badge ${item.matched_skills.includes(skill) ? 'text-bg-success' : 'text-bg-light'}`} key={skill}>{skill}</span>)}</div>}{!item.is_eligible && <div className="alert alert-danger small mt-3 mb-0"><strong>Eligibility requirements:</strong><ul className="mb-0 mt-1">{item.eligibility_reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul></div>}{item.is_eligible && !application && <div className="d-flex justify-content-between align-items-center gap-3 mt-3"><span className="text-success small fw-semibold">You meet the eligibility requirements.</span><button className="btn btn-primary btn-sm" onClick={onApply} type="button">Apply now</button></div>}{application && <div className="d-flex justify-content-between align-items-center gap-3 mt-3"><span className={`application-status status-${application.status.toLowerCase().replace('_', '-')}`}>{application.status_display}</span><Link className="btn btn-sm btn-outline-primary" to="/student/applications">View application</Link></div>}</article></div>
}

function formatDate(value) { return new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`)) }

export default StudentOpportunitiesPage
