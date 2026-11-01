import { ArrowLeft, Award, Plus, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { placementService } from '../../services/placementService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const blankForm = { application_id: '', annual_package: '', offer_date: '', joining_date: '', student_message: '', admin_notes: '', status: 'OFFERED' }
const adminTransitions = { OFFERED: [['ACCEPTED', 'Accepted'], ['DECLINED', 'Declined'], ['CANCELLED', 'Cancelled']], ACCEPTED: [['JOINED', 'Joined'], ['CANCELLED', 'Cancelled']] }

function CollegePlacementsPage() {
  const [applications, setApplications] = useState([])
  const [records, setRecords] = useState([])
  const [form, setForm] = useState(blankForm)
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const recordedApplicationIds = useMemo(() => new Set(records.map((record) => record.application.id)), [records])
  const availableApplications = applications.filter((application) => !recordedApplicationIds.has(application.id))

  useEffect(() => {
    Promise.all([
      placementService.listAdminApplications({ status: 'SELECTED', ordering: '-updated_at' }),
      placementService.listAdminRecords(),
    ]).then(([applicationItems, recordItems]) => {
      setApplications(applicationItems)
      setRecords(recordItems)
    }).catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  const create = async (event) => {
    event.preventDefault()
    setSaving(true)
    try {
      const payload = { ...form, joining_date: form.joining_date || null }
      const created = await placementService.createRecord(payload)
      setRecords((current) => [created, ...current])
      setForm(blankForm)
      setShowForm(false)
      toast.success('Placement record created.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  const updateStatus = async (record, status) => {
    try {
      const updated = await placementService.updateRecord(record.id, { status })
      setRecords((current) => current.map((item) => item.id === updated.id ? updated : item))
      toast.success(`Placement marked as ${updated.status_display.toLowerCase()}.`)
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    }
  }

  return <main className="profile-page"><nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/admin-dashboard"><ArrowLeft size={17} /> Dashboard</Link></nav><div className="container py-5"><div className="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4"><div><p className="eyebrow mb-2">Placement outcomes</p><h1 className="h2 fw-bold mb-2">Placement records</h1><p className="text-secondary mb-0">Verify offers for selected students and track final joining outcomes.</p></div><button className="btn btn-primary d-flex align-items-center gap-2" disabled={!availableApplications.length} onClick={() => setShowForm(true)} type="button"><Plus size={17} /> Record placement</button></div>{showForm && <PlacementForm applications={availableApplications} form={form} onCancel={() => setShowForm(false)} onChange={setForm} onSubmit={create} saving={saving} />}{loading ? <div className="text-center py-5"><div className="spinner-border text-primary" /></div> : records.length ? <div className="row g-4">{records.map((record) => <PlacementCard key={record.id} onStatusChange={(status) => updateStatus(record, status)} record={record} />)}</div> : <div className="profile-card portfolio-empty">No placement records yet. A recruiter must first mark an application as selected.</div>}</div></main>
}

function PlacementForm({ applications, form, onCancel, onChange, onSubmit, saving }) {
  const update = (event) => onChange((current) => ({ ...current, [event.target.name]: event.target.value }))
  return <section className="profile-card mb-4"><div className="d-flex justify-content-between mb-3"><h2 className="h5 fw-bold mb-0">Record verified offer</h2><button aria-label="Close form" className="btn btn-sm btn-light" onClick={onCancel} type="button"><X size={17} /></button></div><form onSubmit={onSubmit}><div className="row g-3"><div className="col-12"><label className="form-label fw-semibold" htmlFor="placement-application">Selected application</label><select className="form-select" id="placement-application" name="application_id" onChange={update} required value={form.application_id}><option value="">Select student and opportunity</option>{applications.map((application) => <option key={application.id} value={application.id}>{candidateName(application)} — {application.opportunity.title} at {application.opportunity.company.name}</option>)}</select></div><div className="col-md-4"><label className="form-label fw-semibold" htmlFor="annual-package">Annual package (INR)</label><input className="form-control" id="annual-package" min="0" name="annual_package" onChange={update} required step="0.01" type="number" value={form.annual_package} /></div><div className="col-md-4"><label className="form-label fw-semibold" htmlFor="offer-date">Offer date</label><input className="form-control" id="offer-date" name="offer_date" onChange={update} required type="date" value={form.offer_date} /></div><div className="col-md-4"><label className="form-label fw-semibold" htmlFor="joining-date">Joining date (optional)</label><input className="form-control" id="joining-date" name="joining_date" onChange={update} type="date" value={form.joining_date} /></div><div className="col-md-6"><label className="form-label fw-semibold" htmlFor="student-message">Message visible to student</label><textarea className="form-control" id="student-message" maxLength="1500" name="student_message" onChange={update} rows="3" value={form.student_message} /></div><div className="col-md-6"><label className="form-label fw-semibold" htmlFor="admin-notes">Private placement-office notes</label><textarea className="form-control" id="admin-notes" maxLength="1500" name="admin_notes" onChange={update} rows="3" value={form.admin_notes} /></div><div className="col-12 text-end"><button className="btn btn-primary" disabled={saving} type="submit">{saving ? 'Saving…' : 'Create placement record'}</button></div></div></form></section>
}

function PlacementCard({ onStatusChange, record }) {
  const application = record.application
  return <div className="col-12 col-lg-6"><article className="profile-card h-100"><div className="d-flex justify-content-between gap-3"><div className="d-flex gap-3"><span className="portfolio-icon"><Award size={20} /></span><div><p className="text-secondary small mb-1">{application.opportunity.company.name} · {application.opportunity.title}</p><h2 className="h5 fw-bold mb-1">{candidateName(application)}</h2><p className="text-secondary small mb-0">{application.student.enrollment_number}</p></div></div><span className={`application-status status-${record.status.toLowerCase()}`}>{record.status_display}</span></div><div className="opportunity-facts mt-3"><span><strong>{formatPackage(record.annual_package)}</strong>annual package</span><span><strong>{formatDate(record.offer_date)}</strong>offer date</span><span><strong>{record.joining_date ? formatDate(record.joining_date) : 'Pending'}</strong>joining date</span></div>{record.student_message && <p className="application-cover-letter mt-3 mb-0">{record.student_message}</p>}{adminTransitions[record.status]?.length > 0 && <div className="d-flex flex-wrap gap-2 mt-3">{adminTransitions[record.status].map(([status, label]) => <button className={`btn btn-sm ${status === 'CANCELLED' || status === 'DECLINED' ? 'btn-outline-danger' : 'btn-outline-success'}`} key={status} onClick={() => onStatusChange(status)} type="button">Mark {label}</button>)}</div>}</article></div>
}

function candidateName(application) { return `${application.student.user.first_name} ${application.student.user.last_name}`.trim() || application.student.user.email }
function formatPackage(value) { return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value)) }
function formatDate(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`)) }

export default CollegePlacementsPage
