import {
  ArrowLeft,
  Check,
  Download,
  FileText,
  Pencil,
  Star,
  Trash2,
  Upload,
  X,
} from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { useConfirmDialog } from '../../hooks/useConfirmDialog.js'
import { studentService } from '../../services/studentService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

function StudentResumePage() {
  const confirmAction = useConfirmDialog()
  const [resumes, setResumes] = useState([])
  const [completion, setCompletion] = useState(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [title, setTitle] = useState('Placement resume')
  const [selectedFile, setSelectedFile] = useState(null)
  const [editing, setEditing] = useState(null)
  const fileInput = useRef(null)

  const refreshCompletion = async () => setCompletion(await studentService.getProfileCompletion())

  useEffect(() => {
    const loadPage = async () => {
      try {
        const [resumeData, completionData] = await Promise.all([
          studentService.getResumes(),
          studentService.getProfileCompletion(),
        ])
        setResumes(resumeData)
        setCompletion(completionData)
      } catch (error) {
        toast.error(getApiErrorMessage(error))
      } finally {
        setLoading(false)
      }
    }
    loadPage()
  }, [])

  const chooseFile = (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    if (file.type !== 'application/pdf' || !file.name.toLowerCase().endsWith('.pdf')) {
      toast.error('Choose a PDF file.')
      setSelectedFile(null)
      event.target.value = ''
      return
    }
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Resume must not exceed 5 MB.')
      setSelectedFile(null)
      event.target.value = ''
      return
    }
    setSelectedFile(file)
  }

  const uploadResume = async (event) => {
    event.preventDefault()
    if (!selectedFile) {
      toast.error('Choose a PDF resume first.')
      return
    }
    setUploading(true)
    const formData = new FormData()
    formData.append('title', title)
    formData.append('file', selectedFile)
    try {
      const resume = await studentService.uploadResume(formData)
      setResumes((current) => [resume, ...current.map((item) => ({ ...item, is_primary: resume.is_primary ? false : item.is_primary }))])
      setTitle('Placement resume')
      setSelectedFile(null)
      if (fileInput.current) fileInput.current.value = ''
      await refreshCompletion()
      toast.success('Resume uploaded successfully.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setUploading(false)
    }
  }

  const updateResume = async (resume, values, successMessage) => {
    try {
      const updated = await studentService.updateResume(resume.id, values)
      setResumes((current) => current.map((item) => ({
        ...item,
        ...(item.id === updated.id ? updated : {}),
        is_primary: values.is_primary ? item.id === updated.id : item.is_primary,
      })))
      setEditing(null)
      await refreshCompletion()
      toast.success(successMessage)
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    }
  }

  const deleteResume = async (resume) => {
    if (!await confirmAction({ title: 'Delete resume?', message: `“${resume.title}” and its uploaded file will be permanently removed.`, confirmLabel: 'Delete resume' })) return
    try {
      await studentService.deleteResume(resume.id)
      const remaining = resumes.filter((item) => item.id !== resume.id)
      if (resume.is_primary && remaining.length) remaining[0] = { ...remaining[0], is_primary: true }
      setResumes(remaining)
      await refreshCompletion()
      toast.success('Resume deleted.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    }
  }

  return (
    <main className="profile-page">
      <nav className="dashboard-nav">
        <div className="d-flex align-items-center gap-2">
          <span className="brand-mark">CC</span>
          <span className="fw-bold fs-5">CampusConnect</span>
        </div>
        <Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/student/dashboard">
          <ArrowLeft aria-hidden="true" size={17} /> Dashboard
        </Link>
      </nav>

      <div className="container py-5">
        <div className="mb-4">
          <p className="eyebrow mb-2">Student workspace</p>
          <h1 className="h2 fw-bold mb-2">Resume centre</h1>
          <p className="text-secondary mb-0">Maintain resume versions and choose the one recruiters should see first.</p>
        </div>

        {loading ? (
          <div className="text-center py-5"><div className="spinner-border text-primary" role="status"><span className="visually-hidden">Loading resumes…</span></div></div>
        ) : (
          <div className="row g-4">
            <div className="col-12 col-lg-8">
              <section className="profile-card mb-4">
                <div className="d-flex align-items-center gap-3 mb-4">
                  <span className="portfolio-icon"><Upload aria-hidden="true" size={20} /></span>
                  <div><h2 className="h5 fw-bold mb-1">Upload a resume version</h2><p className="text-secondary small mb-0">PDF only, maximum 5 MB.</p></div>
                </div>
                <form onSubmit={uploadResume}>
                  <div className="row g-3 align-items-end">
                    <div className="col-12 col-md-5">
                      <label className="form-label fw-semibold" htmlFor="resume-title">Version title</label>
                      <input className="form-control" id="resume-title" maxLength="120" onChange={(event) => setTitle(event.target.value)} required value={title} />
                    </div>
                    <div className="col-12 col-md-7">
                      <label className="form-label fw-semibold" htmlFor="resume-file">PDF file</label>
                      <input accept="application/pdf,.pdf" className="form-control" id="resume-file" onChange={chooseFile} ref={fileInput} required type="file" />
                    </div>
                    <div className="col-12 d-flex justify-content-end">
                      <button className="btn btn-primary d-flex align-items-center gap-2" disabled={uploading} type="submit">
                        <Upload aria-hidden="true" size={17} /> {uploading ? 'Uploading…' : 'Upload resume'}
                      </button>
                    </div>
                  </div>
                </form>
              </section>

              <section className="profile-card">
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <h2 className="h5 fw-bold mb-0">Saved resumes</h2>
                  <span className="badge text-bg-light">{resumes.length} version{resumes.length === 1 ? '' : 's'}</span>
                </div>
                {resumes.length ? (
                  <div className="d-grid gap-3">
                    {resumes.map((resume) => (
                      <ResumeCard
                        editing={editing}
                        key={resume.id}
                        onDelete={() => deleteResume(resume)}
                        onEdit={setEditing}
                        onMakePrimary={() => updateResume(resume, { is_primary: true }, 'Primary resume updated.')}
                        onRename={(newTitle) => updateResume(resume, { title: newTitle }, 'Resume renamed.')}
                        resume={resume}
                      />
                    ))}
                  </div>
                ) : <div className="portfolio-empty">No resume uploaded yet.</div>}
              </section>
            </div>

            <div className="col-12 col-lg-4">
              <CompletionCard completion={completion} />
            </div>
          </div>
        )}
      </div>
    </main>
  )
}

function ResumeCard({ editing, onDelete, onEdit, onMakePrimary, onRename, resume }) {
  const [newTitle, setNewTitle] = useState(resume.title)
  const isEditing = editing === resume.id

  return (
    <article className={`resume-card ${resume.is_primary ? 'resume-card-primary' : ''}`}>
      <div className="resume-file-icon"><FileText aria-hidden="true" size={24} /></div>
      <div className="flex-grow-1 min-width-0">
        {isEditing ? (
          <form className="d-flex gap-2" onSubmit={(event) => { event.preventDefault(); onRename(newTitle) }}>
            <input autoFocus className="form-control form-control-sm" maxLength="120" onChange={(event) => setNewTitle(event.target.value)} required value={newTitle} />
            <button aria-label="Save title" className="btn btn-sm btn-primary" type="submit"><Check size={15} /></button>
            <button aria-label="Cancel editing" className="btn btn-sm btn-light" onClick={() => onEdit(null)} type="button"><X size={15} /></button>
          </form>
        ) : (
          <div className="d-flex flex-wrap align-items-center gap-2">
            <h3 className="h6 fw-bold mb-0 text-truncate">{resume.title}</h3>
            {resume.is_primary && <span className="badge rounded-pill text-bg-primary">Primary</span>}
          </div>
        )}
        <p className="text-secondary small mb-0 mt-1 text-truncate">{resume.original_filename} · {formatFileSize(resume.file_size)} · {formatUploadedDate(resume.updated_at)}</p>
      </div>
      <div className="resume-actions">
        <a aria-label="Open resume" className="btn btn-sm btn-light" href={resume.file_url} rel="noreferrer" target="_blank" title="Open resume"><Download size={16} /></a>
        {!resume.is_primary && <button aria-label="Make primary" className="btn btn-sm btn-light" onClick={onMakePrimary} title="Make primary" type="button"><Star size={16} /></button>}
        <button aria-label="Rename resume" className="btn btn-sm btn-light" onClick={() => { setNewTitle(resume.title); onEdit(resume.id) }} title="Rename" type="button"><Pencil size={16} /></button>
        <button aria-label="Delete resume" className="btn btn-sm btn-light text-danger" onClick={onDelete} title="Delete" type="button"><Trash2 size={16} /></button>
      </div>
    </article>
  )
}

function CompletionCard({ completion }) {
  if (!completion) return null
  return (
    <section className="profile-card completion-card">
      <p className="eyebrow mb-2">Recruiter readiness</p>
      <div className="completion-score" style={{ '--completion': `${completion.percentage * 3.6}deg` }}>
        <div><strong>{completion.percentage}%</strong><span>complete</span></div>
      </div>
      <h2 className="h5 fw-bold text-center mt-3">Profile completion</h2>
      <p className="text-secondary small text-center">This score uses visible profile, portfolio, and resume information.</p>
      <div className="d-grid gap-3 mt-4">
        {completion.sections.map((section) => (
          <div key={section.key}>
            <div className="d-flex justify-content-between small mb-1"><span>{section.label}</span><strong>{section.percentage}%</strong></div>
            <div aria-label={`${section.label}: ${section.percentage}%`} aria-valuemax="100" aria-valuemin="0" aria-valuenow={section.percentage} className="progress" role="progressbar">
              <div className="progress-bar" style={{ width: `${section.percentage}%` }} />
            </div>
          </div>
        ))}
      </div>
      {completion.missing.length > 0 && (
        <div className="completion-next mt-4"><strong>Recommended next:</strong><span>{completion.missing[0]}</span></div>
      )}
    </section>
  )
}

function formatFileSize(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatUploadedDate(value) {
  return new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value))
}

export default StudentResumePage
