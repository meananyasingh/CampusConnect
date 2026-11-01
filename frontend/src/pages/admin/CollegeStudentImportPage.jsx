import { ArrowLeft, CheckCircle2, Download, FileSpreadsheet, History, Upload, XCircle } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { useConfirmDialog } from '../../hooks/useConfirmDialog.js'
import { collegeService } from '../../services/collegeService.js'
import { placementService } from '../../services/placementService.js'
import { studentService } from '../../services/studentService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

function CollegeStudentImportPage() {
  const confirmAction = useConfirmDialog()
  const [programs, setPrograms] = useState([])
  const [history, setHistory] = useState([])
  const [preview, setPreview] = useState(null)
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const fileInput = useRef(null)

  useEffect(() => {
    Promise.all([placementService.getAdminDashboard(), studentService.listImports()])
      .then(async ([dashboard, imports]) => {
        setHistory(imports)
        setPrograms(await collegeService.listPrograms(dashboard.college.id))
      })
      .catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  const downloadTemplate = async () => {
    try {
      await studentService.downloadImportTemplate()
      toast.success('CSV template downloaded.')
    } catch (error) { toast.error(getApiErrorMessage(error)) }
  }

  const validateFile = async (event) => {
    event.preventDefault()
    if (!file) return
    setUploading(true)
    try {
      const batch = await studentService.previewImport(file)
      setPreview(batch)
      setHistory((current) => [batch, ...current.filter((item) => item.id !== batch.id)].slice(0, 20))
      toast.success('CSV validation completed.')
    } catch (error) { toast.error(getApiErrorMessage(error)) } finally { setUploading(false) }
  }

  const confirm = async () => {
    if (!preview?.valid_rows || !await confirmAction({ title: 'Create student accounts?', message: `${preview.valid_rows} student account${preview.valid_rows === 1 ? '' : 's'} will be created and activation emails will be sent.`, confirmLabel: 'Create accounts', tone: 'primary' })) return
    setConfirming(true)
    try {
      const completed = await studentService.confirmImport(preview.id)
      setPreview(completed)
      setHistory((current) => current.map((item) => item.id === completed.id ? completed : item))
      toast.success(`${completed.imported_count} student account${completed.imported_count === 1 ? '' : 's'} created.`)
    } catch (error) { toast.error(getApiErrorMessage(error)) } finally { setConfirming(false) }
  }

  const reset = () => {
    setPreview(null)
    setFile(null)
    if (fileInput.current) fileInput.current.value = ''
  }

  return (
    <main className="profile-page">
      <nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/admin-dashboard"><ArrowLeft size={17} /> Dashboard</Link></nav>
      <div className="container py-5">
        <div className="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4"><div><p className="eyebrow mb-2">Student administration</p><h1 className="h2 fw-bold mb-2">Bulk student onboarding</h1><p className="text-secondary mb-0">Validate student records before creating accounts and sending secure activation links.</p></div><button className="btn btn-outline-primary d-flex align-items-center gap-2" onClick={downloadTemplate} type="button"><Download size={17} /> Download CSV template</button></div>
        {loading ? <Loading /> : <div className="row g-4">
          <div className="col-12 col-xl-4">
            <form className="profile-card" onSubmit={validateFile}>
              <div className="d-flex align-items-center gap-2 mb-3"><span className="portfolio-icon"><Upload size={19} /></span><h2 className="h5 fw-bold mb-0">1. Upload and validate</h2></div>
              <label className="form-label fw-semibold" htmlFor="student-import-file">Student CSV file</label>
              <input accept=".csv,text/csv" className="form-control" id="student-import-file" onChange={(event) => { setFile(event.target.files?.[0] || null); setPreview(null) }} ref={fileInput} required type="file" />
              <p className="small text-secondary mt-2">Maximum 1 MB and 500 rows. Previewing does not create accounts.</p>
              <button className="btn btn-primary w-100" disabled={!file || uploading} type="submit">{uploading ? 'Validating…' : 'Validate and preview'}</button>
            </form>
            <section className="profile-card mt-4"><h2 className="h6 fw-bold mb-3">Program IDs for your CSV</h2>{programs.length ? <div className="import-program-list">{programs.map((program) => <div key={program.id}><code>{program.id}</code><span>{program.degree_display}<small>{program.branch}</small></span></div>)}</div> : <p className="small text-secondary mb-0">No active academic programs are configured.</p>}</section>
            <section className="profile-card mt-4"><h2 className="h6 fw-bold mb-2">Required columns</h2><code className="import-columns">email, first_name, last_name, enrollment_number, program_id, graduation_year, cgpa, active_backlogs</code><p className="small text-secondary mt-2 mb-0">CGPA may be blank. Use 0 when a student has no active backlogs.</p></section>
          </div>
          <div className="col-12 col-xl-8">
            {preview ? <Preview batch={preview} confirming={confirming} onConfirm={confirm} onReset={reset} /> : <section className="profile-card import-placeholder"><FileSpreadsheet size={34} /><h2 className="h5 fw-bold">Your validation preview will appear here</h2><p>Download the template, keep its column names unchanged, and upload the completed CSV.</p></section>}
            <ImportHistory batches={history} />
          </div>
        </div>}
      </div>
    </main>
  )
}

function Preview({ batch, confirming, onConfirm, onReset }) {
  return <section className="profile-card"><div className="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-3"><div><p className="eyebrow mb-1">Validation result</p><h2 className="h5 fw-bold mb-1">{batch.original_filename}</h2><span className={`badge text-bg-${batch.status === 'COMPLETED' ? 'success' : 'primary'}`}>{batch.status_display}</span></div><div className="import-counts"><span className="valid"><strong>{batch.valid_rows}</strong>Valid</span><span className={batch.invalid_rows ? 'invalid' : 'valid'}><strong>{batch.invalid_rows}</strong>Invalid</span></div></div>{batch.invalid_rows > 0 && <div className="alert alert-warning small">Invalid rows will be skipped. Correct them in the CSV and upload again if every student must be included.</div>}<div className="table-responsive import-preview-table"><table className="table align-middle"><thead><tr><th>Row</th><th>Student</th><th>Enrollment</th><th>Program</th><th>Result</th></tr></thead><tbody>{batch.rows.map((row) => <tr key={row.row_number}><td>{row.row_number}</td><td><strong>{row.data.first_name} {row.data.last_name}</strong><small>{row.data.email}</small></td><td>{row.data.enrollment_number || '—'}</td><td>{row.data.program_id || '—'}</td><td>{row.is_valid ? <span className="text-success d-flex align-items-center gap-1"><CheckCircle2 size={16} /> Valid</span> : <div className="import-errors">{Object.entries(row.errors).map(([field, message]) => <span key={field}><XCircle size={14} /> {message}</span>)}</div>}</td></tr>)}</tbody></table></div><div className="d-flex flex-wrap justify-content-end gap-2 mt-3"><button className="btn btn-outline-secondary" onClick={onReset} type="button">Choose another file</button>{batch.status === 'PREVIEW' && <button className="btn btn-success" disabled={!batch.valid_rows || confirming} onClick={onConfirm} type="button">{confirming ? 'Creating accounts…' : `Create ${batch.valid_rows} valid account${batch.valid_rows === 1 ? '' : 's'}`}</button>}{batch.status === 'COMPLETED' && <Link className="btn btn-primary" to="/admin/students">View student directory</Link>}</div></section>
}

function ImportHistory({ batches }) {
  return <section className="profile-card mt-4"><div className="d-flex align-items-center gap-2 mb-3"><History className="text-primary" size={19} /><h2 className="h5 fw-bold mb-0">Recent imports</h2></div>{batches.length ? <div className="import-history">{batches.map((batch) => <div key={batch.id}><span className={`portfolio-icon ${batch.status === 'COMPLETED' ? 'text-success' : ''}`}><FileSpreadsheet size={18} /></span><div><strong>{batch.original_filename}</strong><small>{formatDateTime(batch.created_at)} · {batch.valid_rows} valid, {batch.invalid_rows} invalid</small></div><span className={`badge text-bg-${batch.status === 'COMPLETED' ? 'success' : 'secondary'}`}>{batch.status === 'COMPLETED' ? `${batch.imported_count} imported` : 'Preview only'}</span></div>)}</div> : <p className="portfolio-empty mb-0">No CSV files have been validated yet.</p>}</section>
}

function Loading() { return <div className="text-center py-5"><div className="spinner-border text-primary" /></div> }
function formatDateTime(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) }

export default CollegeStudentImportPage
