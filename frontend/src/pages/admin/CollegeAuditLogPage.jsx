import { Activity, ArrowLeft, Download, Filter, Search } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { auditService } from '../../services/auditService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const initialFilters = { search: '', category: '', actor_role: '', date_from: '', date_to: '' }

function CollegeAuditLogPage() {
  const [events, setEvents] = useState([])
  const [filters, setFilters] = useState(initialFilters)
  const [appliedFilters, setAppliedFilters] = useState(initialFilters)
  const [page, setPage] = useState(1)
  const [count, setCount] = useState(0)
  const [hasNext, setHasNext] = useState(false)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)

  const load = async (requestedPage = 1, requestedFilters = appliedFilters) => {
    setLoading(true)
    try {
      const params = compact({ ...requestedFilters, page: requestedPage })
      const data = await auditService.list(params)
      setEvents(data.results ?? data)
      setCount(data.count ?? data.length)
      setHasNext(Boolean(data.next))
      setPage(requestedPage)
    } catch (error) { toast.error(getApiErrorMessage(error)) } finally { setLoading(false) }
  }

  useEffect(() => {
    auditService.list({ page: 1 })
      .then((data) => {
        setEvents(data.results ?? data)
        setCount(data.count ?? data.length)
        setHasNext(Boolean(data.next))
      })
      .catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  const submit = (event) => {
    event.preventDefault()
    setAppliedFilters(filters)
    load(1, filters)
  }

  const clear = () => {
    setFilters(initialFilters)
    setAppliedFilters(initialFilters)
    load(1, initialFilters)
  }

  const download = async () => {
    setDownloading(true)
    try {
      await auditService.download(compact(appliedFilters))
      toast.success('Audit log CSV downloaded.')
    } catch (error) { toast.error(getApiErrorMessage(error)) } finally { setDownloading(false) }
  }

  return (
    <main className="profile-page">
      <nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/admin-dashboard"><ArrowLeft size={17} /> Dashboard</Link></nav>
      <div className="container py-5">
        <div className="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4"><div><p className="eyebrow mb-2">Governance and accountability</p><h1 className="h2 fw-bold mb-2">Activity and audit log</h1><p className="text-secondary mb-0">A read-only record of successful changes made within your college.</p></div><button className="btn btn-outline-primary d-flex align-items-center gap-2" disabled={downloading} onClick={download} type="button"><Download size={17} /> {downloading ? 'Preparing…' : 'Export filtered CSV'}</button></div>
        <form className="profile-card mb-4" onSubmit={submit}><div className="d-flex align-items-center gap-2 mb-3"><Filter className="text-primary" size={18} /><h2 className="h6 fw-bold mb-0">Filter activity</h2></div><div className="row g-3 align-items-end"><div className="col-12 col-lg-4"><label className="form-label fw-semibold" htmlFor="audit-search">Search</label><div className="input-group"><span className="input-group-text"><Search size={16} /></span><input className="form-control" id="audit-search" onChange={(event) => update(setFilters, 'search', event.target.value)} placeholder="Actor, action, or affected record" value={filters.search} /></div></div><SelectFilter label="Category" name="category" onChange={setFilters} options={categoryOptions} value={filters.category} /><SelectFilter label="Role" name="actor_role" onChange={setFilters} options={roleOptions} value={filters.actor_role} /><DateFilter label="From" name="date_from" onChange={setFilters} value={filters.date_from} /><DateFilter label="To" name="date_to" onChange={setFilters} value={filters.date_to} /><div className="col-12 col-lg-2 d-flex gap-2"><button className="btn btn-outline-secondary flex-grow-1" onClick={clear} type="button">Clear</button><button className="btn btn-primary flex-grow-1" type="submit">Apply</button></div></div></form>
        <div className="d-flex justify-content-between align-items-center mb-3"><h2 className="h5 fw-bold mb-0">Recorded events</h2><span className="badge text-bg-light">{count} event{count === 1 ? '' : 's'}</span></div>
        {loading ? <Loading /> : events.length ? <><div className="audit-event-list">{events.map((event) => <AuditEventCard event={event} key={event.id} />)}</div><div className="d-flex justify-content-between align-items-center mt-4"><button className="btn btn-outline-secondary" disabled={page === 1} onClick={() => load(page - 1)} type="button">Previous</button><span className="small text-secondary">Page {page}</span><button className="btn btn-outline-secondary" disabled={!hasNext} onClick={() => load(page + 1)} type="button">Next</button></div></> : <div className="profile-card portfolio-empty">No activity matches these filters.</div>}
      </div>
    </main>
  )
}

function AuditEventCard({ event }) {
  return <article className="profile-card audit-event-card"><span className={`audit-category category-${event.category.toLowerCase()}`}><Activity size={18} /></span><div className="min-width-0"><div className="d-flex flex-wrap align-items-center gap-2"><strong>{event.action}</strong><span className="badge text-bg-light">{event.category_display}</span><span className="badge text-bg-secondary">{event.actor_role.toLowerCase()}</span></div><p>{event.description}</p><div className="audit-meta"><span>{event.actor_name || event.actor_email}</span><span>{formatDateTime(event.created_at)}</span>{event.ip_address && <span>IP {event.ip_address}</span>}</div>{event.changed_fields.length > 0 && <div className="audit-fields"><small>Changed fields</small>{event.changed_fields.map((field) => <code key={field}>{field.replaceAll('_', ' ')}</code>)}</div>}</div>{event.http_method && <span className={`audit-method method-${event.http_method.toLowerCase()}`}>{event.http_method}</span>}</article>
}

function SelectFilter({ label, name, onChange, options, value }) { return <div className="col-6 col-lg-2"><label className="form-label fw-semibold" htmlFor={`audit-${name}`}>{label}</label><select className="form-select" id={`audit-${name}`} onChange={(event) => update(onChange, name, event.target.value)} value={value}>{options.map(([key, text]) => <option key={key} value={key}>{text}</option>)}</select></div> }
function DateFilter({ label, name, onChange, value }) { return <div className="col-6 col-lg-2"><label className="form-label fw-semibold" htmlFor={`audit-${name}`}>{label}</label><input className="form-control" id={`audit-${name}`} onChange={(event) => update(onChange, name, event.target.value)} type="date" value={value} /></div> }
function update(setter, name, value) { setter((current) => ({ ...current, [name]: value })) }
function compact(values) { return Object.fromEntries(Object.entries(values).filter(([, value]) => value !== '')) }
function Loading() { return <div className="text-center py-5"><div className="spinner-border text-primary" /></div> }
function formatDateTime(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) }

const categoryOptions = [['', 'All categories'], ['ACCOUNT', 'Accounts'], ['COMPANY', 'Companies'], ['OPPORTUNITY', 'Opportunities'], ['APPLICATION', 'Applications'], ['INTERVIEW', 'Interviews'], ['DOCUMENT', 'Documents'], ['PLACEMENT', 'Placements'], ['COMMUNICATION', 'Communications'], ['SYSTEM', 'System']]
const roleOptions = [['', 'All roles'], ['STUDENT', 'Students'], ['RECRUITER', 'Recruiters'], ['ADMIN', 'College admins']]

export default CollegeAuditLogPage
