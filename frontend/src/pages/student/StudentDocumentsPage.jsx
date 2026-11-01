import { ArrowLeft, CheckCircle2, Download, FileCheck2, FileClock, FilePlus2, Trash2, XCircle } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { useConfirmDialog } from '../../hooks/useConfirmDialog.js'
import { documentService } from '../../services/documentService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const documentTypes = [
  ['TENTH_MARKSHEET', '10th marksheet'],
  ['TWELFTH_MARKSHEET', '12th marksheet'],
  ['DIPLOMA_MARKSHEET', 'Diploma marksheet'],
  ['COLLEGE_ID', 'College identity card'],
  ['CURRENT_TRANSCRIPT', 'Current academic transcript'],
  ['DEGREE_CERTIFICATE', 'Degree or provisional certificate'],
  ['OTHER', 'Other placement document'],
]

function StudentDocumentsPage() {
  const confirmAction = useConfirmDialog()
  const [documents, setDocuments] = useState([])
  const [summary, setSummary] = useState(null)
  const [form, setForm] = useState({ document_type: 'TENTH_MARKSHEET', title: '', academic_year: '', student_note: '' })
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const fileInput = useRef(null)

  const load = async () => {
    const [items, readiness] = await Promise.all([documentService.listStudent(), documentService.getSummary()])
    setDocuments(items)
    setSummary(readiness)
  }

  useEffect(() => {
    Promise.all([documentService.listStudent(), documentService.getSummary()])
      .then(([items, readiness]) => { setDocuments(items); setSummary(readiness) })
      .catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  const upload = async (event) => {
    event.preventDefault()
    if (!file) { toast.error('Choose a document file.'); return }
    const payload = new FormData()
    Object.entries(form).forEach(([key, value]) => payload.append(key, value))
    payload.append('file', file)
    setUploading(true)
    try {
      await documentService.upload(payload)
      setForm({ document_type: 'TENTH_MARKSHEET', title: '', academic_year: '', student_note: '' })
      setFile(null)
      if (fileInput.current) fileInput.current.value = ''
      await load()
      toast.success('Document submitted for college verification.')
    } catch (error) { toast.error(getApiErrorMessage(error)) } finally { setUploading(false) }
  }

  const remove = async (document) => {
    if (!await confirmAction({ title: 'Delete document?', message: `“${document.title}” and its uploaded file will be permanently removed.`, confirmLabel: 'Delete document' })) return
    try { await documentService.remove(document.id); await load(); toast.success('Document removed.') } catch (error) { toast.error(getApiErrorMessage(error)) }
  }

  const download = async (document) => {
    try { await documentService.downloadStudent(document) } catch (error) { toast.error(getApiErrorMessage(error)) }
  }

  return <main className="profile-page"><nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/student/dashboard"><ArrowLeft size={17} /> Dashboard</Link></nav><div className="container py-5"><div className="mb-4"><p className="eyebrow mb-2">Student placement record</p><h1 className="h2 fw-bold mb-2">Academic document verification</h1><p className="text-secondary mb-0">Submit clear PDF or image copies for verification by your college placement office.</p></div>{loading ? <Loading /> : <div className="row g-4"><div className="col-12 col-xl-4"><ReadinessCard summary={summary} /><form className="profile-card mt-4" onSubmit={upload}><div className="d-flex gap-2 align-items-center mb-3"><FilePlus2 className="text-primary" size={20} /><h2 className="h5 fw-bold mb-0">Submit document</h2></div><label className="form-label fw-semibold" htmlFor="document-type">Document type</label><select className="form-select mb-3" id="document-type" onChange={(event) => setForm((current) => ({ ...current, document_type: event.target.value }))} value={form.document_type}>{documentTypes.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><label className="form-label fw-semibold" htmlFor="document-title">Title</label><input className="form-control mb-3" id="document-title" maxLength="150" onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} placeholder="e.g. Class 10 CBSE marksheet" required value={form.title} /><label className="form-label fw-semibold" htmlFor="academic-year">Academic year (optional)</label><input className="form-control mb-3" id="academic-year" maxLength="20" onChange={(event) => setForm((current) => ({ ...current, academic_year: event.target.value }))} placeholder="2022-23" value={form.academic_year} /><label className="form-label fw-semibold" htmlFor="document-file">PDF, JPEG, or PNG</label><input accept="application/pdf,image/jpeg,image/png,.pdf,.jpg,.jpeg,.png" className="form-control mb-3" id="document-file" onChange={(event) => setFile(event.target.files?.[0] || null)} ref={fileInput} required type="file" /><label className="form-label fw-semibold" htmlFor="student-note">Note (optional)</label><textarea className="form-control mb-3" id="student-note" maxLength="500" onChange={(event) => setForm((current) => ({ ...current, student_note: event.target.value }))} rows="2" value={form.student_note} /><button className="btn btn-primary w-100" disabled={uploading} type="submit">{uploading ? 'Submitting…' : 'Submit for verification'}</button><p className="small text-secondary mt-2 mb-0">Maximum 5 MB. Files are available only to you and your college placement office.</p></form></div><div className="col-12 col-xl-8"><section className="profile-card"><div className="d-flex justify-content-between align-items-center mb-3"><h2 className="h5 fw-bold mb-0">Submission history</h2><span className="badge text-bg-light">{documents.length} document{documents.length === 1 ? '' : 's'}</span></div>{documents.length ? <div className="document-list">{documents.map((document) => <StudentDocumentCard document={document} key={document.id} onDownload={() => download(document)} onRemove={() => remove(document)} />)}</div> : <div className="portfolio-empty">No documents submitted yet.</div>}</section></div></div>}</div></main>
}

function ReadinessCard({ summary }) { return <section className="profile-card"><div className="document-readiness"><div><span>Verification readiness</span><strong>{summary.percentage}%</strong></div><div className="progress" role="progressbar" aria-valuenow={summary.percentage} aria-valuemin="0" aria-valuemax="100"><div className="progress-bar" style={{ width: `${summary.percentage}%` }} /></div></div><div className="document-requirements mt-3">{summary.requirements.map((item) => <div key={item.key}>{item.status === 'VERIFIED' ? <CheckCircle2 size={17} /> : item.status === 'PENDING' ? <FileClock size={17} /> : <XCircle size={17} />}<span>{item.label}</span><small className={`status-${item.status.toLowerCase()}`}>{item.status.toLowerCase()}</small></div>)}</div></section> }
function StudentDocumentCard({ document, onDownload, onRemove }) { return <article className="student-document-card"><span className="document-file-icon"><FileCheck2 size={22} /></span><div className="min-width-0 flex-grow-1"><div className="d-flex flex-wrap gap-2 align-items-center"><strong>{document.title}</strong><span className={`invitation-status status-${document.status.toLowerCase()}`}>{document.status_display}</span></div><small>{document.document_type_display}{document.academic_year ? ` · ${document.academic_year}` : ''}</small><small>{document.original_filename} · {formatFileSize(document.file_size)} · Submitted {formatDate(document.created_at)}</small>{document.review_note && <p className={document.status === 'REJECTED' ? 'text-danger' : 'text-secondary'}><strong>College note:</strong> {document.review_note}</p>}</div><div className="d-flex gap-1"><button aria-label="Download document" className="btn btn-sm btn-light" onClick={onDownload} type="button"><Download size={16} /></button>{document.status !== 'VERIFIED' && <button aria-label="Delete document" className="btn btn-sm btn-light text-danger" onClick={onRemove} type="button"><Trash2 size={16} /></button>}</div></article> }
function Loading() { return <div className="text-center py-5"><div className="spinner-border text-primary" /></div> }
function formatFileSize(bytes) { return bytes < 1024 * 1024 ? `${Math.ceil(bytes / 1024)} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB` }
function formatDate(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(new Date(value)) }

export default StudentDocumentsPage
