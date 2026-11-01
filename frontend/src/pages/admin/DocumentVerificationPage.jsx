import { ArrowLeft, CheckCircle2, Download, FileSearch, GraduationCap, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { documentService } from '../../services/documentService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const documentTypes = [
  ['', 'All document types'], ['TENTH_MARKSHEET', '10th marksheet'],
  ['TWELFTH_MARKSHEET', '12th marksheet'], ['DIPLOMA_MARKSHEET', 'Diploma marksheet'],
  ['COLLEGE_ID', 'College identity card'], ['CURRENT_TRANSCRIPT', 'Current transcript'],
  ['DEGREE_CERTIFICATE', 'Degree certificate'], ['OTHER', 'Other'],
]

function DocumentVerificationPage() {
  const [documents, setDocuments] = useState([])
  const [statusFilter, setStatusFilter] = useState('PENDING')
  const [typeFilter, setTypeFilter] = useState('')
  const [search, setSearch] = useState('')
  const [notes, setNotes] = useState({})
  const [loading, setLoading] = useState(true)
  const [reviewingId, setReviewingId] = useState(null)

  const load = async (overrides = {}) => {
    setLoading(true)
    const params = {
      ...(statusFilter ? { status: statusFilter } : {}),
      ...(typeFilter ? { document_type: typeFilter } : {}),
      ...(search ? { search } : {}),
      ordering: '-created_at',
      ...overrides,
    }
    Object.keys(params).forEach((key) => params[key] === '' && delete params[key])
    try { setDocuments(await documentService.listAdmin(params)) } catch (error) { toast.error(getApiErrorMessage(error)) } finally { setLoading(false) }
  }

  useEffect(() => {
    documentService.listAdmin({ status: 'PENDING', ordering: '-created_at' })
      .then(setDocuments).catch((error) => toast.error(getApiErrorMessage(error))).finally(() => setLoading(false))
  }, [])

  const review = async (document, status) => {
    const reviewNote = notes[document.id] ?? document.review_note ?? ''
    if (status === 'REJECTED' && !reviewNote.trim()) { toast.error('Add a rejection reason for the student.'); return }
    setReviewingId(document.id)
    try {
      const updated = await documentService.review(document.id, { status, review_note: reviewNote })
      setDocuments((current) => statusFilter && updated.status !== statusFilter ? current.filter((item) => item.id !== updated.id) : current.map((item) => item.id === updated.id ? updated : item))
      toast.success(`Document ${updated.status_display.toLowerCase()}.`)
    } catch (error) { toast.error(getApiErrorMessage(error)) } finally { setReviewingId(null) }
  }

  const download = async (document) => {
    try { await documentService.downloadAdmin(document) } catch (error) { toast.error(getApiErrorMessage(error)) }
  }

  return <main className="profile-page"><nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/admin-dashboard"><ArrowLeft size={17} /> Dashboard</Link></nav><div className="container py-5"><div className="mb-4"><p className="eyebrow mb-2">College placement office</p><h1 className="h2 fw-bold mb-2">Student document verification</h1><p className="text-secondary mb-0">Validate placement documents against college records and give students clear feedback.</p></div><form className="profile-card mb-4" onSubmit={(event) => { event.preventDefault(); load() }}><div className="row g-3 align-items-end"><div className="col-12 col-lg-5"><label className="form-label fw-semibold" htmlFor="document-search">Search students or files</label><input className="form-control" id="document-search" onChange={(event) => setSearch(event.target.value)} placeholder="Name, email, enrollment number, or title" value={search} /></div><div className="col-6 col-lg-3"><label className="form-label fw-semibold" htmlFor="verification-status">Status</label><select className="form-select" id="verification-status" onChange={(event) => setStatusFilter(event.target.value)} value={statusFilter}><option value="">All statuses</option><option value="PENDING">Awaiting verification</option><option value="VERIFIED">Verified</option><option value="REJECTED">Rejected</option></select></div><div className="col-6 col-lg-3"><label className="form-label fw-semibold" htmlFor="document-type-filter">Document type</label><select className="form-select" id="document-type-filter" onChange={(event) => setTypeFilter(event.target.value)} value={typeFilter}>{documentTypes.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div><div className="col-12 col-lg-1"><button className="btn btn-primary w-100" type="submit">Filter</button></div></div></form>{loading ? <Loading /> : documents.length ? <div className="d-grid gap-3">{documents.map((document) => <AdminDocumentCard document={document} key={document.id} note={notes[document.id] ?? document.review_note ?? ''} onDownload={() => download(document)} onNote={(value) => setNotes((current) => ({ ...current, [document.id]: value }))} onReview={review} reviewing={reviewingId === document.id} />)}</div> : <div className="profile-card portfolio-empty">No student documents match these filters.</div>}</div></main>
}

function AdminDocumentCard({ document, note, onDownload, onNote, onReview, reviewing }) { return <article className="profile-card admin-document-card"><header><div className="d-flex gap-3"><span className="portfolio-icon"><FileSearch size={20} /></span><div><h2 className="h5 fw-bold mb-1">{document.title}</h2><p className="text-secondary small mb-1">{document.document_type_display}{document.academic_year ? ` · ${document.academic_year}` : ''}</p><span className={`invitation-status status-${document.status.toLowerCase()}`}>{document.status_display}</span></div></div><button className="btn btn-outline-primary btn-sm d-flex align-items-center gap-1" onClick={onDownload} type="button"><Download size={15} /> Secure download</button></header><div className="student-document-identity mt-3"><GraduationCap size={19} /><div><strong>{document.student.name}</strong><small>{document.student.enrollment_number} · {document.student.program} · Class of {document.student.graduation_year}</small><small>{document.student.email}</small></div></div>{document.student_note && <p className="recruiter-request-message mt-3 mb-0"><strong>Student note</strong>{document.student_note}</p>}<label className="form-label fw-semibold small mt-3" htmlFor={`document-review-${document.id}`}>Review note {document.status === 'PENDING' && '(required for rejection)'}</label><textarea className="form-control" disabled={document.status !== 'PENDING'} id={`document-review-${document.id}`} maxLength="1000" onChange={(event) => onNote(event.target.value)} placeholder="Explain any mismatch or record an approval note" rows="2" value={note} />{document.status === 'PENDING' && <div className="d-flex flex-wrap gap-2 mt-3"><button className="btn btn-success btn-sm d-flex align-items-center gap-1" disabled={reviewing} onClick={() => onReview(document, 'VERIFIED')} type="button"><CheckCircle2 size={15} /> Verify document</button><button className="btn btn-outline-danger btn-sm d-flex align-items-center gap-1" disabled={reviewing} onClick={() => onReview(document, 'REJECTED')} type="button"><XCircle size={15} /> Reject with reason</button></div>}</article> }
function Loading() { return <div className="text-center py-5"><div className="spinner-border text-primary" /></div> }

export default DocumentVerificationPage
