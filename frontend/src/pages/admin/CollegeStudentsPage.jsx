import { ArrowLeft, MailPlus, Search, ShieldCheck, ShieldOff, UserRound } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { useConfirmDialog } from '../../hooks/useConfirmDialog.js'
import { analyticsService } from '../../services/analyticsService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

function CollegeStudentsPage() {
  const confirmAction = useConfirmDialog()
  const [students, setStudents] = useState([])
  const [count, setCount] = useState(0)
  const [search, setSearch] = useState('')
  const [activeFilter, setActiveFilter] = useState('')
  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)
  const [loading, setLoading] = useState(true)
  const [updatingId, setUpdatingId] = useState(null)

  const receive = (data, requestedPage) => {
    setStudents(data.results ?? data)
    setCount(data.count ?? data.length)
    setHasNext(Boolean(data.next))
    setPage(requestedPage)
  }

  const load = async (requestedPage = page) => {
    setLoading(true)
    try {
      receive(await analyticsService.listStudents({
        page: requestedPage,
        ...(search ? { search } : {}),
        ...(activeFilter ? { user__is_active: activeFilter } : {}),
        ordering: 'user__first_name',
      }), requestedPage)
    } catch (error) { toast.error(getApiErrorMessage(error)) } finally { setLoading(false) }
  }

  useEffect(() => {
    analyticsService.listStudents({ page: 1, ordering: 'user__first_name' })
      .then((data) => receive(data, 1))
      .catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  const replaceStudent = (updated) => {
    setStudents((current) => current.map((item) => item.id === updated.id ? updated : item))
  }

  const setAccountStatus = async (student, accountIsActive) => {
    const action = accountIsActive ? 'activate' : 'suspend'
    if (!await confirmAction({ title: `${action[0].toUpperCase()}${action.slice(1)} student account?`, message: `${student.user.first_name || student.user.email} will ${accountIsActive ? 'regain access to' : 'lose access to'} CampusConnect.`, confirmLabel: accountIsActive ? 'Activate account' : 'Suspend account', tone: accountIsActive ? 'primary' : 'danger' })) return
    setUpdatingId(student.id)
    try {
      replaceStudent(await analyticsService.updateStudent(student.id, { account_is_active: accountIsActive }))
      toast.success(`Student account ${accountIsActive ? 'activated' : 'suspended'}.`)
    } catch (error) { toast.error(getApiErrorMessage(error)) } finally { setUpdatingId(null) }
  }

  const resendActivation = async (student) => {
    setUpdatingId(student.id)
    try {
      replaceStudent(await analyticsService.resendStudentActivation(student.id))
      toast.success('A fresh activation link was sent. Check the Django terminal during local development.')
    } catch (error) { toast.error(getApiErrorMessage(error)) } finally { setUpdatingId(null) }
  }

  return (
    <main className="profile-page">
      <nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/admin-dashboard"><ArrowLeft size={17} /> Dashboard</Link></nav>
      <div className="container py-5">
        <div className="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4"><div><p className="eyebrow mb-2">Student administration</p><h1 className="h2 fw-bold mb-2">Student directory</h1><p className="text-secondary mb-0">Search, manage, and monitor activation for {count} students in your college.</p></div><Link className="btn btn-primary" to="/admin/student-imports">Import students</Link></div>
        <form className="profile-card mb-4" onSubmit={(event) => { event.preventDefault(); load(1) }}><div className="row g-3 align-items-end"><div className="col-12 col-md-8"><label className="form-label fw-semibold" htmlFor="student-search">Search students</label><div className="input-group"><span className="input-group-text"><Search size={17} /></span><input className="form-control" id="student-search" onChange={(event) => setSearch(event.target.value)} placeholder="Name, email, enrollment number, branch" value={search} /></div></div><div className="col-8 col-md-3"><label className="form-label fw-semibold" htmlFor="student-status">Account status</label><select className="form-select" id="student-status" onChange={(event) => setActiveFilter(event.target.value)} value={activeFilter}><option value="">All</option><option value="true">Active</option><option value="false">Suspended</option></select></div><div className="col-4 col-md-1"><button className="btn btn-primary w-100" type="submit">Go</button></div></div></form>
        {loading ? <Loading /> : students.length ? <><div className="row g-4">{students.map((student) => <StudentCard key={student.id} onActivation={() => resendActivation(student)} onStatusChange={(value) => setAccountStatus(student, value)} student={student} updating={updatingId === student.id} />)}</div><div className="d-flex justify-content-between align-items-center mt-4"><button className="btn btn-outline-secondary" disabled={page === 1} onClick={() => load(page - 1)} type="button">Previous</button><span className="text-secondary small">Page {page}</span><button className="btn btn-outline-secondary" disabled={!hasNext} onClick={() => load(page + 1)} type="button">Next</button></div></> : <div className="profile-card portfolio-empty">No students match the current filters.</div>}
      </div>
    </main>
  )
}

function StudentCard({ onActivation, onStatusChange, student, updating }) {
  const name = `${student.user.first_name} ${student.user.last_name}`.trim() || student.user.email
  const pending = student.activation_status === 'PENDING'
  return <div className="col-12 col-lg-6"><article className="profile-card h-100"><div className="d-flex justify-content-between gap-3"><div className="d-flex gap-3"><span className="portfolio-icon"><UserRound size={20} /></span><div><h2 className="h5 fw-bold mb-1">{name}</h2><p className="text-secondary small mb-0">{student.user.email}</p><p className="text-secondary small mb-0">{student.enrollment_number}</p></div></div><div className="d-grid gap-1 justify-items-end"><span className={`badge text-bg-${student.account_is_active ? 'success' : 'secondary'}`}>{student.account_is_active ? 'Active' : 'Suspended'}</span><span className={`badge text-bg-${pending ? 'warning' : 'light'}`}>{pending ? 'Invitation pending' : 'Account activated'}</span></div></div><dl className="profile-details mt-3 mb-0"><dt>Program</dt><dd>{student.program.degree_display} — {student.program.branch}</dd><dt>Graduation</dt><dd>{student.graduation_year}</dd><dt>CGPA</dt><dd>{student.cgpa ?? 'Not provided'}</dd><dt>Backlogs</dt><dd>{student.active_backlogs}</dd>{pending && <><dt>Invitation</dt><dd>{student.activation_email_sent_at ? `Sent ${formatDateTime(student.activation_email_sent_at)} · ${student.activation_email_count} time(s)` : 'Not sent yet'}</dd></>}</dl><div className="d-flex flex-wrap justify-content-end gap-2 mt-3">{pending && <button className="btn btn-sm btn-outline-primary d-inline-flex align-items-center gap-1" disabled={updating} onClick={onActivation} type="button"><MailPlus size={15} /> Resend activation</button>}{student.account_is_active ? <button className="btn btn-sm btn-outline-danger d-inline-flex align-items-center gap-1" disabled={updating} onClick={() => onStatusChange(false)} type="button"><ShieldOff size={15} /> Suspend</button> : <button className="btn btn-sm btn-outline-success d-inline-flex align-items-center gap-1" disabled={updating} onClick={() => onStatusChange(true)} type="button"><ShieldCheck size={15} /> Restore</button>}</div></article></div>
}

function Loading() { return <div className="text-center py-5"><div className="spinner-border text-primary" /></div> }
function formatDateTime(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) }

export default CollegeStudentsPage
