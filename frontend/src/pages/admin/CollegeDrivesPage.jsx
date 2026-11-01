import { ArrowLeft, Building2, CalendarDays, FileCheck2, MapPin, Pencil, Plus, Trash2, UserRoundCheck, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { useConfirmDialog } from '../../hooks/useConfirmDialog.js'
import { placementService } from '../../services/placementService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const blankForm = { title: '', description: '', start_date: '', end_date: '', venue: '', opportunity_ids: [] }
const transitions = { DRAFT: [['UPCOMING', 'Publish drive']], UPCOMING: [['ONGOING', 'Start drive'], ['CANCELLED', 'Cancel']], ONGOING: [['COMPLETED', 'Complete drive'], ['CANCELLED', 'Cancel']] }

function CollegeDrivesPage() {
  const confirmAction = useConfirmDialog()
  const [drives, setDrives] = useState([])
  const [opportunities, setOpportunities] = useState([])
  const [form, setForm] = useState(blankForm)
  const [editingId, setEditingId] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    Promise.all([placementService.listAdminDrives(), placementService.listDriveOpportunities()])
      .then(([driveItems, opportunityItems]) => { setDrives(driveItems); setOpportunities(opportunityItems) })
      .catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  const openCreate = () => { setEditingId(null); setForm(blankForm); setShowForm(true) }
  const openEdit = (drive) => { setEditingId(drive.id); setForm({ title: drive.title, description: drive.description, start_date: drive.start_date, end_date: drive.end_date, venue: drive.venue, opportunity_ids: drive.opportunities.map((item) => String(item.id)) }); setShowForm(true); window.scrollTo({ top: 0, behavior: 'smooth' }) }
  const update = (event) => { const { checked, name, value } = event.target; if (name === 'opportunity_ids') setForm((current) => ({ ...current, opportunity_ids: checked ? [...current.opportunity_ids, value] : current.opportunity_ids.filter((id) => id !== value) })); else setForm((current) => ({ ...current, [name]: value })) }
  const save = async (event) => {
    event.preventDefault(); setSaving(true)
    try {
      const saved = editingId ? await placementService.updateDrive(editingId, form) : await placementService.createDrive({ ...form, status: 'DRAFT' })
      setDrives((current) => editingId ? current.map((item) => item.id === saved.id ? saved : item) : [saved, ...current])
      setShowForm(false); setEditingId(null); setForm(blankForm); toast.success(editingId ? 'Placement drive updated.' : 'Placement drive created as a draft.')
    } catch (error) { toast.error(getApiErrorMessage(error)) } finally { setSaving(false) }
  }
  const changeStatus = async (drive, status) => {
    try { const updated = await placementService.updateDrive(drive.id, { status }); setDrives((current) => current.map((item) => item.id === updated.id ? updated : item)); toast.success(`Drive marked as ${updated.status_display.toLowerCase()}.`) } catch (error) { toast.error(getApiErrorMessage(error)) }
  }
  const remove = async (drive) => {
    if (!await confirmAction({ title: 'Delete draft drive?', message: `“${drive.title}” will be permanently removed.`, confirmLabel: 'Delete drive' })) return
    try { await placementService.deleteDrive(drive.id); setDrives((current) => current.filter((item) => item.id !== drive.id)); toast.success('Draft drive deleted.') } catch (error) { toast.error(getApiErrorMessage(error)) }
  }

  return <main className="profile-page"><nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/admin-dashboard"><ArrowLeft size={17} /> Dashboard</Link></nav><div className="container py-5"><div className="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4"><div><p className="eyebrow mb-2">Placement coordination</p><h1 className="h2 fw-bold mb-2">Placement drives</h1><p className="text-secondary mb-0">Group approved opportunities into scheduled campus hiring events and monitor their progress.</p></div><button className="btn btn-primary d-flex align-items-center gap-2" onClick={openCreate} type="button"><Plus size={17} /> Create drive</button></div>{showForm && <DriveForm editing={Boolean(editingId)} form={form} onCancel={() => setShowForm(false)} onChange={update} onSubmit={save} opportunities={opportunities} saving={saving} />}{loading ? <Loading /> : drives.length ? <div className="d-grid gap-4">{drives.map((drive) => <AdminDriveCard drive={drive} key={drive.id} onDelete={() => remove(drive)} onEdit={() => openEdit(drive)} onStatus={(status) => changeStatus(drive, status)} />)}</div> : <div className="profile-card portfolio-empty">No placement drives created yet.</div>}</div></main>
}

function DriveForm({ editing, form, onCancel, onChange, onSubmit, opportunities, saving }) {
  return <section className="profile-card mb-4"><div className="d-flex justify-content-between align-items-center mb-3"><h2 className="h5 fw-bold mb-0">{editing ? 'Edit drive' : 'New placement drive'}</h2><button aria-label="Close" className="btn btn-sm btn-light" onClick={onCancel} type="button"><X size={17} /></button></div><form onSubmit={onSubmit}><div className="row g-3"><Field label="Drive title" name="title" onChange={onChange} required value={form.title} /><Field label="Venue or coordination details" name="venue" onChange={onChange} value={form.venue} /><Field label="Start date" name="start_date" onChange={onChange} required type="date" value={form.start_date} /><Field label="End date" min={form.start_date} name="end_date" onChange={onChange} required type="date" value={form.end_date} /><div className="col-12"><label className="form-label fw-semibold" htmlFor="drive-description">Description</label><textarea className="form-control" id="drive-description" maxLength="2500" name="description" onChange={onChange} rows="3" value={form.description} /></div><div className="col-12"><label className="form-label fw-semibold">Included opportunities</label><div className="drive-opportunity-picker">{opportunities.length ? opportunities.map((item) => <label key={item.id}><input checked={form.opportunity_ids.includes(String(item.id))} name="opportunity_ids" onChange={onChange} type="checkbox" value={item.id} /><span><strong>{item.title}</strong><small>{item.company.name} · {item.status_display}</small></span></label>) : <div className="portfolio-empty">No published, college-approved opportunities are currently available.</div>}</div></div></div><div className="d-flex justify-content-end gap-2 mt-4"><button className="btn btn-outline-secondary" onClick={onCancel} type="button">Cancel</button><button className="btn btn-primary" disabled={saving} type="submit">{saving ? 'Saving…' : editing ? 'Save changes' : 'Create draft'}</button></div></form></section>
}
function Field({ label, name, onChange, type = 'text', value, ...props }) { return <div className="col-12 col-md-6"><label className="form-label fw-semibold" htmlFor={`drive-${name}`}>{label}</label><input className="form-control" id={`drive-${name}`} name={name} onChange={onChange} type={type} value={value} {...props} /></div> }
function AdminDriveCard({ drive, onDelete, onEdit, onStatus }) { const editable = ['DRAFT', 'UPCOMING'].includes(drive.status); return <article className="profile-card"><div className="d-flex flex-wrap justify-content-between gap-3"><div><div className="d-flex gap-2 mb-2"><span className={`application-status status-${drive.status.toLowerCase()}`}>{drive.status_display}</span><span className="badge text-bg-light">{drive.college.code}</span></div><h2 className="h4 fw-bold mb-1">{drive.title}</h2><p className="text-secondary small mb-0"><CalendarDays size={15} /> {formatDate(drive.start_date)} – {formatDate(drive.end_date)}{drive.venue && <> · <MapPin size={15} /> {drive.venue}</>}</p></div><div className="d-flex gap-1">{editable && <button aria-label="Edit drive" className="btn btn-sm btn-light" onClick={onEdit} type="button"><Pencil size={16} /></button>}{drive.status === 'DRAFT' && <button aria-label="Delete drive" className="btn btn-sm btn-light text-danger" onClick={onDelete} type="button"><Trash2 size={16} /></button>}</div></div>{drive.description && <p className="portfolio-description small mt-3 mb-0">{drive.description}</p>}<div className="drive-metrics"><span><Building2 size={17} /><strong>{drive.company_count}</strong> companies</span><span><FileCheck2 size={17} /><strong>{drive.opportunity_count}</strong> opportunities</span><span><FileCheck2 size={17} /><strong>{drive.application_count}</strong> applications</span><span><UserRoundCheck size={17} /><strong>{drive.interview_count}</strong> interviews</span><span><UserRoundCheck size={17} /><strong>{drive.selected_count}</strong> selected</span></div><div className="drive-opportunities">{drive.opportunities.map((item) => <span key={item.id}><strong>{item.company.name}</strong>{item.title}</span>)}</div>{transitions[drive.status]?.length > 0 && <div className="d-flex flex-wrap gap-2 mt-3">{transitions[drive.status].map(([status, label]) => <button className={`btn btn-sm ${status === 'CANCELLED' ? 'btn-outline-danger' : 'btn-outline-primary'}`} key={status} onClick={() => onStatus(status)} type="button">{label}</button>)}</div>}</article> }
function Loading() { return <div className="text-center py-5"><div className="spinner-border text-primary" /></div> }
function formatDate(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`)) }

export default CollegeDrivesPage
