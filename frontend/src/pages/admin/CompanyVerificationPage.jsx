import { ArrowLeft, Building2, CheckCircle2, ExternalLink, ShieldAlert, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { companyService } from '../../services/companyService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const filters = [
  ['', 'All'],
  ['PENDING', 'Pending'],
  ['VERIFIED', 'Verified'],
  ['REJECTED', 'Rejected'],
  ['SUSPENDED', 'Suspended'],
]

function CompanyVerificationPage() {
  const [partnerships, setPartnerships] = useState([])
  const [statusFilter, setStatusFilter] = useState('PENDING')
  const [notes, setNotes] = useState({})
  const [loading, setLoading] = useState(true)
  const [reviewingId, setReviewingId] = useState(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        setPartnerships(await companyService.listPartnerships(statusFilter))
      } catch (error) {
        toast.error(getApiErrorMessage(error))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [statusFilter])

  const review = async (partnership, status) => {
    setReviewingId(partnership.id)
    try {
      const updated = await companyService.reviewPartnership(partnership.id, {
        status,
        review_note: notes[partnership.id] ?? partnership.review_note ?? '',
      })
      if (statusFilter && status !== statusFilter) {
        setPartnerships((current) => current.filter((item) => item.id !== updated.id))
      } else {
        setPartnerships((current) => current.map((item) => item.id === updated.id ? updated : item))
      }
      toast.success(`Company marked as ${updated.status_display.toLowerCase()}.`)
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setReviewingId(null)
    }
  }

  return (
    <main className="profile-page">
      <nav className="dashboard-nav">
        <div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div>
        <Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/admin-dashboard"><ArrowLeft size={17} /> Dashboard</Link>
      </nav>
      <div className="container py-5">
        <div className="d-flex flex-wrap justify-content-between align-items-end gap-3 mb-4">
          <div><p className="eyebrow mb-2">College administration</p><h1 className="h2 fw-bold mb-2">Company recruitment requests</h1><p className="text-secondary mb-0">Review companies that want to recruit students from your college and send them a response.</p></div>
          <div className="d-flex align-items-end gap-2"><Link className="btn btn-outline-primary" to="/admin/opportunity-requests">Opportunity requests</Link><div><label className="form-label small fw-semibold" htmlFor="status-filter">Verification status</label><select className="form-select" id="status-filter" onChange={(event) => setStatusFilter(event.target.value)} value={statusFilter}>{filters.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div></div>
        </div>

        {loading ? <div className="text-center py-5"><div className="spinner-border text-primary" /></div> : partnerships.length ? (
          <div className="row g-4">
            {partnerships.map((partnership) => (
              <div className="col-12 col-lg-6" key={partnership.id}>
                <article className="profile-card h-100">
                  <div className="d-flex align-items-start gap-3">
                    <span className="portfolio-icon"><Building2 size={20} /></span>
                    <div className="flex-grow-1 min-width-0"><h2 className="h5 fw-bold mb-1">{partnership.company.name}</h2><p className="text-secondary small mb-1">{partnership.company.industry} · {partnership.company.contact_email}</p><span className={`badge text-bg-${statusColor(partnership.status)}`}>{partnership.status_display}</span></div>
                  </div>
                  {partnership.company.description && <p className="small text-secondary mt-3">{partnership.company.description}</p>}
                  <div className="d-flex flex-wrap gap-3 my-3"><a className="portfolio-link" href={partnership.company.website} rel="noreferrer" target="_blank">Company website <ExternalLink size={13} /></a>{partnership.company.linkedin_url && <a className="portfolio-link" href={partnership.company.linkedin_url} rel="noreferrer" target="_blank">LinkedIn <ExternalLink size={13} /></a>}</div>
                  <label className="form-label small fw-semibold" htmlFor={`note-${partnership.id}`}>Review note</label>
                  <textarea className="form-control" id={`note-${partnership.id}`} maxLength="500" onChange={(event) => setNotes((current) => ({ ...current, [partnership.id]: event.target.value }))} placeholder="Optional reason or verification note" rows="2" value={notes[partnership.id] ?? partnership.review_note ?? ''} />
                  <div className="d-flex flex-wrap gap-2 mt-3">
                    <button className="btn btn-success btn-sm d-flex align-items-center gap-1" disabled={reviewingId === partnership.id} onClick={() => review(partnership, 'VERIFIED')} type="button"><CheckCircle2 size={15} /> Approve request</button>
                    <button className="btn btn-outline-danger btn-sm d-flex align-items-center gap-1" disabled={reviewingId === partnership.id} onClick={() => review(partnership, 'REJECTED')} type="button"><XCircle size={15} /> Decline request</button>
                    <button className="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1" disabled={reviewingId === partnership.id} onClick={() => review(partnership, 'SUSPENDED')} type="button"><ShieldAlert size={15} /> Pause recruitment</button>
                  </div>
                </article>
              </div>
            ))}
          </div>
        ) : <div className="profile-card portfolio-empty">No companies match this verification status.</div>}
      </div>
    </main>
  )
}

function statusColor(status) {
  return { PENDING: 'warning', VERIFIED: 'success', REJECTED: 'danger', SUSPENDED: 'secondary' }[status]
}

export default CompanyVerificationPage
