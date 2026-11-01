import { ArrowLeft, Award, Building2, CalendarCheck2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { useConfirmDialog } from '../../hooks/useConfirmDialog.js'
import { placementService } from '../../services/placementService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

function StudentPlacementsPage() {
  const confirmAction = useConfirmDialog()
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [savingId, setSavingId] = useState(null)

  useEffect(() => {
    placementService.listStudent()
      .then(setRecords)
      .catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  const decide = async (record, status) => {
    const accepting = status === 'ACCEPTED'
    if (!await confirmAction({ title: `${accepting ? 'Accept' : 'Decline'} this offer?`, message: `You are about to ${accepting ? 'accept' : 'decline'} the offer from ${record.application.opportunity.company.name}.`, confirmLabel: accepting ? 'Accept offer' : 'Decline offer', tone: accepting ? 'primary' : 'danger' })) return
    setSavingId(record.id)
    try {
      const updated = await placementService.decideOffer(record.id, status)
      setRecords((current) => current.map((item) => item.id === updated.id ? updated : item))
      toast.success(`Offer ${updated.status_display.toLowerCase()}.`)
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setSavingId(null)
    }
  }

  return <main className="profile-page"><nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/student/dashboard"><ArrowLeft size={17} /> Dashboard</Link></nav><div className="container py-5"><div className="mb-4"><p className="eyebrow mb-2">Placement outcomes</p><h1 className="h2 fw-bold mb-2">My placement offers</h1><p className="text-secondary mb-0">Review verified offers and record your decision securely.</p></div>{loading ? <div className="text-center py-5"><div className="spinner-border text-primary" /></div> : records.length ? <div className="row g-4">{records.map((record) => <div className="col-12 col-lg-6" key={record.id}><article className="profile-card h-100"><div className="d-flex justify-content-between gap-3"><span className="portfolio-icon"><Award size={20} /></span><span className={`application-status status-${record.status.toLowerCase()}`}>{record.status_display}</span></div><h2 className="h4 fw-bold mt-3 mb-1">{record.application.opportunity.title}</h2><p className="text-secondary mb-3"><Building2 size={16} /> {record.application.opportunity.company.name}</p><div className="opportunity-facts"><span><strong>{formatPackage(record.annual_package)}</strong>annual package</span><span><strong>{formatDate(record.offer_date)}</strong>offer date</span><span><strong>{record.joining_date ? formatDate(record.joining_date) : 'Pending'}</strong>joining date</span></div>{record.student_message && <p className="application-cover-letter mt-3 mb-0">{record.student_message}</p>}{record.status === 'OFFERED' && <div className="d-flex gap-2 mt-4"><button className="btn btn-success" disabled={savingId === record.id} onClick={() => decide(record, 'ACCEPTED')} type="button"><CalendarCheck2 size={16} /> Accept offer</button><button className="btn btn-outline-danger" disabled={savingId === record.id} onClick={() => decide(record, 'DECLINED')} type="button">Decline</button></div>}</article></div>)}</div> : <div className="profile-card portfolio-empty">No verified placement offers have been recorded yet.</div>}</div></main>
}

function formatPackage(value) { return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value)) }
function formatDate(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`)) }

export default StudentPlacementsPage
