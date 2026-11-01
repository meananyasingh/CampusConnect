import {
  ArrowLeft, BookmarkPlus, BriefcaseBusiness, Download, ExternalLink, FileText,
  FolderPlus, GraduationCap, Search, Trash2, UserRound, UsersRound, X,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { useConfirmDialog } from '../../hooks/useConfirmDialog.js'
import { companyService } from '../../services/companyService.js'
import { talentService } from '../../services/talentService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const emptyFilters = {
  search: '', college: '', graduation_year: '', min_cgpa: '', max_backlogs: '',
  skill: '', has_resume: '', ordering: '-cgpa',
}

function RecruiterTalentPage() {
  const [activeTab, setActiveTab] = useState('candidates')
  const [candidates, setCandidates] = useState([])
  const [candidateCount, setCandidateCount] = useState(0)
  const [pools, setPools] = useState([])
  const [colleges, setColleges] = useState([])
  const [filters, setFilters] = useState(emptyFilters)
  const [selectedCandidate, setSelectedCandidate] = useState(null)
  const [loading, setLoading] = useState(true)
  const [creatingPool, setCreatingPool] = useState(false)
  const [poolForm, setPoolForm] = useState({ name: '', description: '' })

  const loadCandidates = async (params = filters) => {
    setLoading(true)
    try {
      const data = await talentService.listCandidates(cleanParams(params))
      setCandidates(data.results ?? data)
      setCandidateCount(data.count ?? data.length)
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  const loadPools = async () => {
    try {
      setPools(await talentService.listPools())
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    }
  }

  useEffect(() => {
    Promise.all([talentService.listCandidates({ ordering: '-cgpa' }), talentService.listPools(), companyService.getRecruiterProfile()])
      .then(([candidateData, poolData, profile]) => {
        setCandidates(candidateData.results ?? candidateData)
        setCandidateCount(candidateData.count ?? candidateData.length)
        setPools(poolData)
        setColleges(profile.company.partnerships.filter((item) => item.status === 'VERIFIED').map((item) => item.college))
      })
      .catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  const openCandidate = async (id) => {
    try {
      setSelectedCandidate(await talentService.getCandidate(id))
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    }
  }

  const createPool = async (event) => {
    event.preventDefault()
    setCreatingPool(true)
    try {
      await talentService.createPool(poolForm)
      setPoolForm({ name: '', description: '' })
      await loadPools()
      toast.success('Private talent pool created.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setCreatingPool(false)
    }
  }

  return (
    <main className="profile-page">
      <nav className="dashboard-nav">
        <div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div>
        <Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/recruiter/dashboard"><ArrowLeft size={17} /> Dashboard</Link>
      </nav>
      <div className="container py-5">
        <div className="d-flex flex-wrap justify-content-between align-items-end gap-3 mb-4">
          <div><p className="eyebrow mb-2">Verified college talent network</p><h1 className="h2 fw-bold mb-2">Candidate discovery</h1><p className="text-secondary mb-0">Find recruiter-visible students and organize promising profiles privately.</p></div>
          <span className="badge rounded-pill text-bg-primary px-3 py-2">{candidateCount} discoverable candidates</span>
        </div>

        <div className="talent-tabs mb-4" role="tablist">
          <button className={activeTab === 'candidates' ? 'active' : ''} onClick={() => setActiveTab('candidates')} type="button"><Search size={17} /> Discover candidates</button>
          <button className={activeTab === 'pools' ? 'active' : ''} onClick={() => setActiveTab('pools')} type="button"><UsersRound size={17} /> Private pools <span>{pools.length}</span></button>
        </div>

        {activeTab === 'candidates' ? <>
          <CandidateFilters colleges={colleges} filters={filters} onChange={setFilters} onReset={() => { setFilters(emptyFilters); loadCandidates(emptyFilters) }} onSubmit={() => loadCandidates()} />
          {loading ? <Loading /> : candidates.length ? <div className="candidate-grid">{candidates.map((candidate) => <CandidateCard candidate={candidate} key={candidate.id} onOpen={openCandidate} />)}</div> : <div className="profile-card portfolio-empty">No visible candidates match these filters. Try broadening your search.</div>}
        </> : <div className="row g-4">
          <div className="col-12 col-lg-4"><form className="profile-card" onSubmit={createPool}><div className="d-flex align-items-center gap-2 mb-3"><FolderPlus className="text-primary" size={20} /><h2 className="h5 fw-bold mb-0">Create a private pool</h2></div><label className="form-label fw-semibold" htmlFor="pool-name">Pool name</label><input className="form-control mb-3" id="pool-name" maxLength="120" onChange={(event) => setPoolForm((current) => ({ ...current, name: event.target.value }))} placeholder="e.g. Backend shortlist" required value={poolForm.name} /><label className="form-label fw-semibold" htmlFor="pool-description">Description</label><textarea className="form-control mb-3" id="pool-description" maxLength="500" onChange={(event) => setPoolForm((current) => ({ ...current, description: event.target.value }))} rows="3" value={poolForm.description} /><button className="btn btn-primary w-100" disabled={creatingPool} type="submit">{creatingPool ? 'Creating…' : 'Create pool'}</button><p className="small text-secondary mt-3 mb-0">Pools are shared only with recruiters from your company.</p></form></div>
          <div className="col-12 col-lg-8">{pools.length ? <div className="d-grid gap-3">{pools.map((pool) => <TalentPoolCard key={pool.id} onChanged={loadPools} onOpenCandidate={openCandidate} pool={pool} />)}</div> : <div className="profile-card portfolio-empty">No talent pools yet. Create one to organize candidates.</div>}</div>
        </div>}
      </div>
      {selectedCandidate && <CandidateModal candidate={selectedCandidate} onClose={() => setSelectedCandidate(null)} onPoolChanged={loadPools} pools={pools} />}
    </main>
  )
}

function CandidateFilters({ colleges, filters, onChange, onReset, onSubmit }) {
  const update = (field, value) => onChange((current) => ({ ...current, [field]: value }))
  return <form className="profile-card mb-4" onSubmit={(event) => { event.preventDefault(); onSubmit() }}><div className="row g-3 align-items-end"><div className="col-12 col-lg-4"><label className="form-label fw-semibold" htmlFor="talent-search">Search</label><div className="input-group"><span className="input-group-text"><Search size={16} /></span><input className="form-control" id="talent-search" onChange={(event) => update('search', event.target.value)} placeholder="Name, skill, branch, or role" value={filters.search} /></div></div><FilterSelect id="talent-college" label="College" onChange={(value) => update('college', value)} value={filters.college}><option value="">All approved colleges</option>{colleges.map((college) => <option key={college.id} value={college.id}>{college.name}</option>)}</FilterSelect><FilterInput field="skill" filters={filters} label="Skill" onChange={update} placeholder="e.g. Python" /><FilterInput field="graduation_year" filters={filters} label="Graduation year" min="2020" onChange={update} type="number" /><FilterInput field="min_cgpa" filters={filters} label="Minimum CGPA" max="10" min="0" onChange={update} step="0.1" type="number" /><FilterInput field="max_backlogs" filters={filters} label="Maximum backlogs" min="0" onChange={update} type="number" /><FilterSelect id="talent-resume" label="Resume" onChange={(value) => update('has_resume', value)} value={filters.has_resume}><option value="">Any</option><option value="true">Primary resume available</option><option value="false">No primary resume</option></FilterSelect><FilterSelect id="talent-sort" label="Sort by" onChange={(value) => update('ordering', value)} value={filters.ordering}><option value="-cgpa">Highest CGPA</option><option value="user__first_name">Candidate name</option><option value="graduation_year">Graduation year</option><option value="-updated_at">Recently updated</option></FilterSelect><div className="col-12 d-flex justify-content-end gap-2"><button className="btn btn-outline-secondary" onClick={onReset} type="button">Reset</button><button className="btn btn-primary" type="submit">Apply filters</button></div></div></form>
}

function FilterInput({ field, filters, label, onChange, ...props }) { return <div className="col-6 col-lg-2"><label className="form-label fw-semibold small" htmlFor={`filter-${field}`}>{label}</label><input className="form-control" id={`filter-${field}`} onChange={(event) => onChange(field, event.target.value)} value={filters[field]} {...props} /></div> }
function FilterSelect({ children, id, label, onChange, value }) { return <div className="col-6 col-lg-2"><label className="form-label fw-semibold small" htmlFor={id}>{label}</label><select className="form-select" id={id} onChange={(event) => onChange(event.target.value)} value={value}>{children}</select></div> }

function CandidateCard({ candidate, onOpen }) {
  const name = `${candidate.first_name} ${candidate.last_name}`.trim() || 'Student candidate'
  return <article className="profile-card candidate-card"><div className="d-flex gap-3"><CandidateAvatar candidate={candidate} /><div className="min-width-0"><h2 className="h5 fw-bold mb-1">{name}</h2><p className="text-primary fw-semibold small mb-1">{candidate.preferred_job_role || 'Open to placement roles'}</p><p className="text-secondary small mb-0">{candidate.program.branch} · Class of {candidate.graduation_year}</p><p className="text-secondary small mb-0">{candidate.college.name}</p></div></div><div className="candidate-metrics"><span><strong>{candidate.cgpa ?? '—'}</strong>CGPA</span><span><strong>{candidate.active_backlogs}</strong>Backlogs</span><span><strong>{candidate.profile_completion}%</strong>Profile</span></div><div className="candidate-skills">{candidate.skills.slice(0, 5).map((skill) => <span key={skill.name}>{skill.name}</span>)}{!candidate.skills.length && <small className="text-secondary">No skills listed</small>}</div><button className="btn btn-outline-primary w-100" onClick={() => onOpen(candidate.id)} type="button">View professional profile</button></article>
}

function CandidateAvatar({ candidate }) { return candidate.profile_picture ? <img alt="" className="candidate-avatar" src={candidate.profile_picture} /> : <span className="candidate-avatar candidate-avatar-placeholder"><UserRound size={25} /></span> }

function CandidateModal({ candidate, onClose, onPoolChanged, pools }) {
  const [poolId, setPoolId] = useState('')
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const name = `${candidate.first_name} ${candidate.last_name}`.trim()
  const add = async () => {
    if (!poolId) return
    setSaving(true)
    try {
      await talentService.addMember(poolId, { student_id: candidate.id, private_notes: notes })
      await onPoolChanged()
      toast.success(`${name} added to the talent pool.`)
      setPoolId(''); setNotes('')
    } catch (error) { toast.error(getApiErrorMessage(error)) } finally { setSaving(false) }
  }
  const download = async () => { try { await talentService.downloadResume(candidate) } catch (error) { toast.error(getApiErrorMessage(error)) } }
  return <div className="talent-modal-backdrop" onMouseDown={onClose} role="presentation"><section aria-modal="true" className="talent-modal" onMouseDown={(event) => event.stopPropagation()} role="dialog"><header><div className="d-flex gap-3"><CandidateAvatar candidate={candidate} /><div><h2 className="h4 fw-bold mb-1">{name}</h2><p className="text-primary fw-semibold mb-1">{candidate.preferred_job_role || 'Student candidate'}</p><small className="text-secondary">{candidate.program.degree_display}, {candidate.program.branch} · {candidate.college.name}</small></div></div><button aria-label="Close candidate profile" className="btn btn-light" onClick={onClose} type="button"><X size={20} /></button></header><div className="talent-modal-body"><div className="candidate-metrics mb-3"><span><strong>{candidate.cgpa ?? '—'}</strong>CGPA</span><span><strong>{candidate.active_backlogs}</strong>Backlogs</span><span><strong>{candidate.graduation_year}</strong>Graduation</span><span><strong>{candidate.profile_completion}%</strong>Profile</span></div>{candidate.career_objective && <p className="candidate-objective">{candidate.career_objective}</p>}<ProfileLinks candidate={candidate} /><ProfileSection icon={GraduationCap} title="Skills"><div className="candidate-skills">{candidate.skills.map((skill) => <span key={skill.name}>{skill.name} · {skill.proficiency_display}</span>)}</div></ProfileSection><ProfileSection icon={BriefcaseBusiness} title="Experience">{candidate.experiences.length ? candidate.experiences.map((item) => <ProfileRecord key={item.id} subtitle={`${item.organization} · ${item.employment_type.toLowerCase().replace('_', ' ')}`} title={item.role} />) : <EmptyLine text="No experience added." />}</ProfileSection><ProfileSection icon={FileText} title="Projects">{candidate.projects.length ? candidate.projects.map((item) => <ProfileRecord key={item.id} subtitle={item.technologies} text={item.description} title={item.title} />) : <EmptyLine text="No projects added." />}</ProfileSection><ProfileSection icon={GraduationCap} title="Certifications">{candidate.certifications.length ? candidate.certifications.map((item) => <ProfileRecord key={item.id} subtitle={item.issuing_organization} title={item.name} />) : <EmptyLine text="No certifications added." />}</ProfileSection>{candidate.primary_resume && <button className="btn btn-outline-primary d-flex align-items-center gap-2 mb-4" onClick={download} type="button"><Download size={17} /> Download primary resume</button>}<section className="pool-add-panel"><h3 className="h6 fw-bold"><BookmarkPlus className="me-2 text-primary" size={18} />Add to private pool</h3>{pools.length ? <div className="row g-2"><div className="col-md-5"><select className="form-select" onChange={(event) => setPoolId(event.target.value)} value={poolId}><option value="">Choose pool</option>{pools.map((pool) => <option key={pool.id} value={pool.id}>{pool.name}</option>)}</select></div><div className="col-md-5"><input className="form-control" maxLength="1000" onChange={(event) => setNotes(event.target.value)} placeholder="Private note (optional)" value={notes} /></div><div className="col-md-2"><button className="btn btn-primary w-100" disabled={!poolId || saving} onClick={add} type="button">Add</button></div></div> : <p className="small text-secondary mb-0">Create a talent pool from the Private pools tab first.</p>}</section></div></section></div>
}

function ProfileLinks({ candidate }) { const links = [[candidate.email, `mailto:${candidate.email}`], ['LinkedIn', candidate.linkedin_url], ['GitHub', candidate.github_url], ['Portfolio', candidate.portfolio_url]].filter(([, url]) => url); return <div className="candidate-links">{links.map(([label, url]) => <a href={url} key={label} rel="noreferrer" target={url.startsWith('mailto:') ? undefined : '_blank'}>{label} <ExternalLink size={13} /></a>)}</div> }
function ProfileSection({ children, icon: Icon, title }) { return <section className="candidate-profile-section"><h3><Icon size={18} />{title}</h3>{children}</section> }
function ProfileRecord({ subtitle, text, title }) { return <div className="candidate-record"><strong>{title}</strong>{subtitle && <small>{subtitle}</small>}{text && <p>{text}</p>}</div> }
function EmptyLine({ text }) { return <p className="small text-secondary mb-0">{text}</p> }

function TalentPoolCard({ onChanged, onOpenCandidate, pool }) {
  const confirmAction = useConfirmDialog()
  const [open, setOpen] = useState(true)
  const removePool = async () => { if (!await confirmAction({ title: 'Delete talent pool?', message: `“${pool.name}” and its saved candidate list will be removed. Student profiles will not be affected.`, confirmLabel: 'Delete pool' })) return; try { await talentService.deletePool(pool.id); await onChanged(); toast.success('Talent pool deleted.') } catch (error) { toast.error(getApiErrorMessage(error)) } }
  const removeMember = async (member) => { try { await talentService.removeMember(pool.id, member.id); await onChanged(); toast.success('Candidate removed from pool.') } catch (error) { toast.error(getApiErrorMessage(error)) } }
  return <section className="profile-card talent-pool-card"><header><button className="talent-pool-heading" onClick={() => setOpen((value) => !value)} type="button"><UsersRound size={20} /><span><strong>{pool.name}</strong><small>{pool.description || 'Private company shortlist'} · {pool.member_count} candidate{pool.member_count === 1 ? '' : 's'}</small></span></button><button aria-label={`Delete ${pool.name}`} className="btn btn-sm btn-outline-danger" onClick={removePool} type="button"><Trash2 size={16} /></button></header>{open && <div className="talent-pool-members">{pool.members.length ? pool.members.map((member) => <PoolMember key={member.id} member={member} onChanged={onChanged} onOpen={onOpenCandidate} onRemove={() => removeMember(member)} poolId={pool.id} />) : <div className="portfolio-empty py-3">No candidates saved in this pool.</div>}</div>}</section>
}

function PoolMember({ member, onChanged, onOpen, onRemove, poolId }) {
  const [notes, setNotes] = useState(member.private_notes || '')
  const [saving, setSaving] = useState(false)
  const student = member.student
  const name = `${student.first_name} ${student.last_name}`.trim()
  const save = async () => { setSaving(true); try { await talentService.updateMember(poolId, member.id, { private_notes: notes }); await onChanged(); toast.success('Private note saved.') } catch (error) { toast.error(getApiErrorMessage(error)) } finally { setSaving(false) } }
  return <article className="pool-member"><div className="d-flex gap-2 align-items-center"><CandidateAvatar candidate={student} /><div><button className="candidate-name-button" onClick={() => onOpen(student.id)} type="button">{name}</button><small>{student.program.branch} · CGPA {student.cgpa ?? '—'}</small></div></div><div className="pool-note"><input className="form-control form-control-sm" maxLength="1000" onChange={(event) => setNotes(event.target.value)} placeholder="Add a private note" value={notes} /><button className="btn btn-sm btn-outline-primary" disabled={saving || notes === (member.private_notes || '')} onClick={save} type="button">Save note</button><button aria-label={`Remove ${name}`} className="btn btn-sm btn-outline-danger" onClick={onRemove} type="button"><Trash2 size={15} /></button></div></article>
}

function Loading() { return <div className="text-center py-5"><div className="spinner-border text-primary" /></div> }
function cleanParams(params) { return Object.fromEntries(Object.entries(params).filter(([, value]) => value !== '')) }

export default RecruiterTalentPage
