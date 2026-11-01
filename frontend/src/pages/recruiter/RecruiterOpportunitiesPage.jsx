import { ArrowLeft, MapPin, Pencil, Plus, Save, Trash2, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { useConfirmDialog } from '../../hooks/useConfirmDialog.js'
import { collegeService } from '../../services/collegeService.js'
import { companyService } from '../../services/companyService.js'
import { opportunityService } from '../../services/opportunityService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const blankForm = {
  title: '', opportunity_type: 'JOB', description: '', responsibilities: '', qualifications: '',
  location: '', work_mode: 'ONSITE', openings: '1', compensation_min: '', compensation_max: '',
  compensation_period: 'YEAR', application_deadline: '', min_cgpa: '0', max_active_backlogs: '0',
  graduation_year_from: '', graduation_year_to: '', target_college_ids: [], eligible_program_ids: [],
  required_skills_text: '', status: 'DRAFT',
}

function RecruiterOpportunitiesPage() {
  const confirmAction = useConfirmDialog()
  const [opportunities, setOpportunities] = useState([])
  const [verifiedColleges, setVerifiedColleges] = useState([])
  const [programs, setPrograms] = useState([])
  const [editor, setEditor] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(blankForm)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [shareItem, setShareItem] = useState(null)
  const [shareColleges, setShareColleges] = useState([])
  const [sharePrograms, setSharePrograms] = useState([])
  const [shareMessage, setShareMessage] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const [items, recruiter] = await Promise.all([
          opportunityService.listRecruiter(),
          companyService.getRecruiterProfile(),
        ])
        setOpportunities(items)
        const verified = recruiter.company.partnerships
          .filter((item) => item.status === 'VERIFIED')
          .map((item) => item.college)
        setVerifiedColleges(verified)
        const programLists = await Promise.all(verified.map((college) => collegeService.listPrograms(college.id)))
        setPrograms(programLists.flat())
      } catch (error) {
        toast.error(getApiErrorMessage(error))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const updateForm = (event) => {
    const { name, options, type, value } = event.target
    if (type === 'select-multiple') {
      const selected = [...options].filter((option) => option.selected).map((option) => option.value)
      setForm((current) => ({
        ...current,
        [name]: selected,
        ...(name === 'target_college_ids'
          ? { eligible_program_ids: current.eligible_program_ids.filter((programId) => {
              const program = programs.find((item) => String(item.id) === String(programId))
              return program && selected.includes(String(program.college))
            }) }
          : {}),
      }))
    } else {
      setForm((current) => ({ ...current, [name]: value }))
    }
  }

  const openNew = () => {
    setEditingId(null)
    setForm(blankForm)
    setEditor(true)
  }

  const openEdit = (item) => {
    setEditingId(item.id)
    setForm({
      ...blankForm,
      ...item,
      target_college_ids: item.target_colleges.map((college) => String(college.id)),
      eligible_program_ids: item.eligible_programs.map((program) => String(program.id)),
      required_skills_text: item.required_skills.join(', '),
    })
    setEditor(true)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const save = async (event) => {
    event.preventDefault()
    setSaving(true)
    const nullable = ['compensation_min', 'compensation_max', 'graduation_year_from', 'graduation_year_to']
    const payload = {
      ...form,
      required_skill_names: form.required_skills_text.split(',').map((value) => value.trim()).filter(Boolean),
    }
    if (!editingId) {
      payload.status = 'DRAFT'
      payload.target_college_ids = []
      payload.eligible_program_ids = []
    }
    delete payload.required_skills_text
    delete payload.target_college_ids
    delete payload.eligible_program_ids
    nullable.forEach((field) => { if (payload[field] === '') payload[field] = null })
    try {
      const saved = editingId
        ? await opportunityService.update(editingId, payload)
        : await opportunityService.create(payload)
      setOpportunities((current) => editingId
        ? current.map((item) => item.id === saved.id ? saved : item)
        : [saved, ...current])
      setEditor(false)
      setEditingId(null)
      toast.success(editingId ? 'Opportunity updated.' : 'Opportunity created.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  const changeStatus = async (item, status) => {
    try {
      const updated = await opportunityService.update(item.id, { status })
      setOpportunities((current) => current.map((entry) => entry.id === updated.id ? updated : entry))
      toast.success(`Opportunity marked as ${updated.status_display.toLowerCase()}.`)
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    }
  }

  const openCollegeShare = (item) => {
    setShareItem(item)
    setShareColleges([])
    setSharePrograms([])
    setShareMessage('')
  }

  const sendToColleges = async (event) => {
    event.preventDefault()
    setSaving(true)
    try {
      const updated = await opportunityService.sendToColleges(shareItem.id, {
        college_ids: shareColleges,
        eligible_program_ids: sharePrograms,
        recruiter_message: shareMessage,
      })
      setOpportunities((current) => current.map((entry) => entry.id === updated.id ? updated : entry))
      setShareItem(null)
      toast.success('Opportunity sent to the selected colleges.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  const withdrawInvitation = async (item, invitation) => {
    try {
      await opportunityService.withdrawInvitation(invitation.id)
      const updated = await opportunityService.getRecruiter(item.id)
      setOpportunities((current) => current.map((entry) => entry.id === updated.id ? updated : entry))
      toast.success('Pending college invitation withdrawn.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    }
  }

  const remove = async (item) => {
    if (!await confirmAction({ title: 'Delete draft opportunity?', message: `“${item.title}” will be permanently removed.`, confirmLabel: 'Delete opportunity' })) return
    try {
      await opportunityService.remove(item.id)
      setOpportunities((current) => current.filter((entry) => entry.id !== item.id))
      toast.success('Draft deleted.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    }
  }

  return (
    <main className="profile-page">
      <nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/recruiter/dashboard"><ArrowLeft size={17} /> Dashboard</Link></nav>
      <div className="container py-5">
        <div className="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4"><div><p className="eyebrow mb-2">Recruiter workspace</p><h1 className="h2 fw-bold mb-2">Jobs and internships</h1><p className="text-secondary mb-0">Create an opportunity, then send it to one or more approved colleges.</p></div><button className="btn btn-primary d-flex align-items-center gap-2" onClick={openNew} type="button"><Plus size={17} /> Create opportunity</button></div>
        {editor && <OpportunityEditor form={form} onCancel={() => setEditor(false)} onChange={updateForm} onSave={save} saving={saving} />}
        {shareItem && <CollegeShareEditor colleges={verifiedColleges} item={shareItem} message={shareMessage} onCancel={() => setShareItem(null)} onCollegesChange={setShareColleges} onMessageChange={setShareMessage} onProgramsChange={setSharePrograms} onSave={sendToColleges} programs={programs} saving={saving} selectedColleges={shareColleges} selectedPrograms={sharePrograms} />}
        {loading ? <div className="text-center py-5"><div className="spinner-border text-primary" /></div> : (
          <section className="profile-card"><h2 className="h5 fw-bold mb-3">Your company’s opportunities</h2>{opportunities.length ? <div className="d-grid gap-3">{opportunities.map((item) => <RecruiterOpportunityCard item={item} key={item.id} onDelete={() => remove(item)} onEdit={() => openEdit(item)} onShare={() => openCollegeShare(item)} onStatus={(status) => changeStatus(item, status)} onWithdraw={(invitation) => withdrawInvitation(item, invitation)} />)}</div> : <div className="portfolio-empty">No opportunities created yet.</div>}</section>
        )}
      </div>
    </main>
  )
}

function OpportunityEditor({ form, onCancel, onChange, onSave, saving }) {
  return <section className="profile-card mb-4"><div className="d-flex justify-content-between mb-3"><h2 className="h5 fw-bold mb-0">Opportunity editor</h2><button aria-label="Close editor" className="btn btn-sm btn-light" onClick={onCancel} type="button"><X size={17} /></button></div><form onSubmit={onSave}><div className="row g-3">
    <Field label="Title" name="title" onChange={onChange} required value={form.title} />
    <SelectField label="Type" name="opportunity_type" onChange={onChange} options={[['JOB', 'Job'], ['INTERNSHIP', 'Internship']]} value={form.opportunity_type} />
    <Field full label="Description" name="description" onChange={onChange} required rows="4" type="textarea" value={form.description} />
    <Field full label="Responsibilities" name="responsibilities" onChange={onChange} rows="3" type="textarea" value={form.responsibilities} />
    <Field full label="Qualifications" name="qualifications" onChange={onChange} rows="3" type="textarea" value={form.qualifications} />
    <Field label="Location" name="location" onChange={onChange} required value={form.location} />
    <SelectField label="Work mode" name="work_mode" onChange={onChange} options={[['ONSITE', 'On-site'], ['REMOTE', 'Remote'], ['HYBRID', 'Hybrid']]} value={form.work_mode} />
    <Field label="Openings" min="1" name="openings" onChange={onChange} required type="number" value={form.openings} />
    <Field label="Application deadline" name="application_deadline" onChange={onChange} required type="date" value={form.application_deadline} />
    <Field label="Minimum compensation" min="0" name="compensation_min" onChange={onChange} step="0.01" type="number" value={form.compensation_min} />
    <Field label="Maximum compensation" min="0" name="compensation_max" onChange={onChange} step="0.01" type="number" value={form.compensation_max} />
    <SelectField label="Compensation period" name="compensation_period" onChange={onChange} options={[['YEAR', 'Per year'], ['MONTH', 'Per month']]} value={form.compensation_period} />
    <Field label="Minimum CGPA" max="10" min="0" name="min_cgpa" onChange={onChange} step="0.01" type="number" value={form.min_cgpa} />
    <Field label="Maximum active backlogs" min="0" name="max_active_backlogs" onChange={onChange} type="number" value={form.max_active_backlogs} />
    <Field label="Graduation year from" name="graduation_year_from" onChange={onChange} type="number" value={form.graduation_year_from} />
    <Field label="Graduation year to" name="graduation_year_to" onChange={onChange} type="number" value={form.graduation_year_to} />
    <Field full label="Required skills (comma separated)" name="required_skills_text" onChange={onChange} placeholder="Django, React, MySQL" value={form.required_skills_text} />
  </div><div className="d-flex justify-content-end gap-2 mt-4"><button className="btn btn-outline-secondary" onClick={onCancel} type="button">Cancel</button><button className="btn btn-primary d-flex align-items-center gap-2" disabled={saving} type="submit"><Save size={17} /> {saving ? 'Saving…' : form.id ? 'Save changes' : 'Create opportunity'}</button></div></form></section>
}

function CollegeShareEditor({ colleges, item, message, onCancel, onCollegesChange, onMessageChange, onProgramsChange, onSave, programs, saving, selectedColleges, selectedPrograms }) {
  const selectedCollegeIds = new Set(selectedColleges.map(String))
  const visiblePrograms = programs.filter((program) => selectedCollegeIds.has(String(program.college)))
  const selectValues = (event) => [...event.target.options].filter((option) => option.selected).map((option) => option.value)
  return <section className="profile-card mb-4"><div className="d-flex justify-content-between gap-3 mb-3"><div><p className="eyebrow mb-1">College hiring</p><h2 className="h5 fw-bold mb-0">Send “{item.title}” for review</h2></div><button aria-label="Close" className="btn btn-sm btn-light" onClick={onCancel} type="button"><X size={17} /></button></div>{colleges.length ? <form onSubmit={onSave}><div className="row g-3"><div className="col-12 col-md-6"><label className="form-label fw-semibold" htmlFor="share-colleges">Verified partner colleges</label><select className="form-select" id="share-colleges" multiple onChange={(event) => { const values = selectValues(event); onCollegesChange(values); onProgramsChange((current) => current.filter((id) => { const program = programs.find((entry) => String(entry.id) === String(id)); return program && values.includes(String(program.college)) })) }} required size={Math.max(2, Math.min(5, colleges.length))} value={selectedColleges}>{colleges.map((college) => <option key={college.id} value={college.id}>{college.name}</option>)}</select><small className="text-secondary">Each college reviews this opportunity independently.</small></div><div className="col-12 col-md-6"><label className="form-label fw-semibold" htmlFor="share-programs">Eligible programs</label><select className="form-select" id="share-programs" multiple onChange={(event) => onProgramsChange(selectValues(event))} size="5" value={selectedPrograms}>{visiblePrograms.map((program) => <option key={program.id} value={program.id}>{program.degree_display} — {program.branch}</option>)}</select><small className="text-secondary">Leave empty to include every program in each selected college.</small></div><div className="col-12"><label className="form-label fw-semibold" htmlFor="share-message">Message to placement office (optional)</label><textarea className="form-control" id="share-message" maxLength="1000" onChange={(event) => onMessageChange(event.target.value)} placeholder="Share hiring context or coordination details" rows="2" value={message} /></div></div><div className="d-flex justify-content-end gap-2 mt-4"><button className="btn btn-outline-secondary" onClick={onCancel} type="button">Cancel</button><button className="btn btn-primary" disabled={saving || !selectedColleges.length} type="submit">{saving ? 'Sending…' : 'Send for college review'}</button></div></form> : <div className="alert alert-warning mb-0">No college has approved your company yet. Send recruitment requests from the company profile first.</div>}</section>
}

function Field({ full = false, label, name, onChange, type = 'text', value, ...props }) {
  return <div className={full ? 'col-12' : 'col-12 col-md-6'}><label className="form-label fw-semibold" htmlFor={name}>{label}</label>{type === 'textarea' ? <textarea className="form-control" id={name} name={name} onChange={onChange} value={value} {...props} /> : <input className="form-control" id={name} name={name} onChange={onChange} type={type} value={value} {...props} />}</div>
}

function SelectField({ label, name, onChange, options, value }) {
  return <div className="col-12 col-md-6"><label className="form-label fw-semibold" htmlFor={name}>{label}</label><select className="form-select" id={name} name={name} onChange={onChange} value={value}>{options.map(([key, text]) => <option key={key} value={key}>{text}</option>)}</select></div>
}

function RecruiterOpportunityCard({ item, onDelete, onEdit, onShare, onStatus, onWithdraw }) {
  const colors = { DRAFT: 'secondary', PUBLISHED: 'success', CLOSED: 'dark', CANCELLED: 'danger' }
  const collegeCount = item.target_colleges.length
  const pendingCount = item.college_invitations.filter((invitation) => invitation.status === 'PENDING').length
  return <article className="opportunity-card"><div className="d-flex justify-content-between gap-3"><div><div className="d-flex flex-wrap gap-2 mb-2"><span className={`badge text-bg-${colors[item.status]}`}>{item.status_display}</span><span className="badge text-bg-light">{item.opportunity_type_display}</span><span className="badge text-bg-info-subtle">{collegeCount ? `${collegeCount} college approval${collegeCount === 1 ? '' : 's'}` : pendingCount ? 'Awaiting college review' : 'Not submitted yet'}</span></div><h3 className="h5 fw-bold mb-1">{item.title}</h3><p className="text-secondary small mb-0"><MapPin size={14} /> {item.location} · {item.work_mode_display} · Deadline {formatDate(item.application_deadline)}</p></div><div className="d-flex gap-1"><button aria-label="Edit" className="btn btn-sm btn-light" onClick={onEdit} type="button"><Pencil size={16} /></button>{item.status === 'DRAFT' && !item.college_invitations.length && <button aria-label="Delete" className="btn btn-sm btn-light text-danger" onClick={onDelete} type="button"><Trash2 size={16} /></button>}</div></div><p className="small mt-3 mb-2">{item.description}</p><div className="d-flex flex-wrap gap-2">{item.required_skills.map((skill) => <span className="badge text-bg-light" key={skill}>{skill}</span>)}</div>{item.college_invitations.length > 0 && <div className="invitation-status-list mt-3">{item.college_invitations.map((invitation) => <div key={invitation.id}><span><strong>{invitation.college.name}</strong><small className={`invitation-status status-${invitation.status.toLowerCase()}`}>{invitation.status_display}</small></span>{invitation.review_note && <p>{invitation.review_note}</p>}{invitation.status === 'PENDING' && <button className="btn btn-sm btn-link text-danger" onClick={() => onWithdraw(invitation)} type="button">Withdraw</button>}</div>)}</div>}{['DRAFT', 'PUBLISHED'].includes(item.status) && <div className="d-flex flex-wrap gap-2 mt-3"><button className="btn btn-sm btn-outline-primary" onClick={onShare} type="button">Send or resubmit to colleges</button>{item.status === 'PUBLISHED' && <><Link className="btn btn-sm btn-outline-success" to={`/recruiter/applications?opportunity=${item.id}`}>View applicants</Link><Link className="btn btn-sm btn-outline-primary" to={`/recruiter/opportunities/${item.id}/process`}>Recruitment process</Link><button className="btn btn-sm btn-outline-dark" onClick={() => onStatus('CLOSED')} type="button">Close</button><button className="btn btn-sm btn-outline-danger" onClick={() => onStatus('CANCELLED')} type="button">Cancel</button></>}</div>}</article>
}

function formatDate(value) { return new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`)) }

export default RecruiterOpportunitiesPage
