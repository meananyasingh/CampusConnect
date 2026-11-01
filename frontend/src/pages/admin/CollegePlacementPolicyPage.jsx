import { ArrowLeft, Save, ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { placementService } from '../../services/placementService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const emptyPolicy = {
  applications_enabled: true,
  require_verified_documents: false,
  minimum_profile_completion: '0',
  minimum_cgpa: '',
  max_active_backlogs: '',
  student_message: '',
}

function CollegePlacementPolicyPage() {
  const [policy, setPolicy] = useState(emptyPolicy)
  const [college, setCollege] = useState(null)
  const [updatedAt, setUpdatedAt] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    placementService.getAdminPolicy()
      .then((data) => {
        setCollege(data.college)
        setUpdatedAt(data.updated_at)
        setPolicy(toFormValues(data))
      })
      .catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  const change = (event) => {
    const { checked, name, type, value } = event.target
    setPolicy((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
  }

  const save = async (event) => {
    event.preventDefault()
    setSaving(true)
    try {
      const data = await placementService.updateAdminPolicy({
        ...policy,
        minimum_profile_completion: Number(policy.minimum_profile_completion),
        minimum_cgpa: policy.minimum_cgpa === '' ? null : policy.minimum_cgpa,
        max_active_backlogs: policy.max_active_backlogs === '' ? null : Number(policy.max_active_backlogs),
      })
      setPolicy(toFormValues(data))
      setUpdatedAt(data.updated_at)
      toast.success('Placement policy updated.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  return (
    <main className="profile-page">
      <nav className="dashboard-nav">
        <div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div>
        <Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/admin-dashboard"><ArrowLeft size={17} /> Dashboard</Link>
      </nav>
      <div className="container py-5 policy-page-width">
        <div className="mb-4">
          <p className="eyebrow mb-2">College placement office</p>
          <h1 className="h2 fw-bold mb-2">Placement participation policy</h1>
          <p className="text-secondary mb-0">Set the common requirements students must satisfy before applying to campus opportunities at {college?.name || 'your college'}.</p>
        </div>
        <div className="policy-information mb-4"><ShieldCheck size={22} /><p><strong>How this works</strong><span>These rules are checked together with every company’s opportunity-specific eligibility. Students can still browse opportunities and see exactly what they need to complete.</span></p></div>
        {loading ? <Loading /> : <form className="profile-card" onSubmit={save}>
          <PolicySwitch checked={policy.applications_enabled} description="Turn this off only when the college needs to temporarily pause all new applications." label="Allow students to submit applications" name="applications_enabled" onChange={change} />
          <PolicySwitch checked={policy.require_verified_documents} description="Requires verified 10th, 12th or diploma, and college identity documents." label="Require core document verification" name="require_verified_documents" onChange={change} />
          <hr className="my-4" />
          <div className="row g-4">
            <PolicyNumber help="Set 0 to allow any profile completion level." label="Minimum profile completion (%)" max="100" min="0" name="minimum_profile_completion" onChange={change} required value={policy.minimum_profile_completion} />
            <PolicyNumber help="Leave blank when the college has no common CGPA rule." label="Minimum CGPA" max="10" min="0" name="minimum_cgpa" onChange={change} step="0.01" value={policy.minimum_cgpa} />
            <PolicyNumber help="Leave blank when backlogs are not restricted college-wide." label="Maximum active backlogs" min="0" name="max_active_backlogs" onChange={change} value={policy.max_active_backlogs} />
          </div>
          <div className="mt-4">
            <label className="form-label fw-semibold" htmlFor="student_message">Message shown when applications are paused</label>
            <textarea className="form-control" id="student_message" maxLength="500" name="student_message" onChange={change} placeholder="For example: Applications are paused during semester examinations." rows="3" value={policy.student_message} />
            <div className="form-text">If left blank, CampusConnect shows a standard pause message.</div>
          </div>
          <div className="d-flex flex-wrap justify-content-between align-items-center gap-3 mt-4">
            <small className="text-secondary">{updatedAt ? `Last updated ${formatDateTime(updatedAt)}` : 'Using the default open policy.'}</small>
            <button className="btn btn-primary d-flex align-items-center gap-2" disabled={saving} type="submit"><Save size={17} /> {saving ? 'Saving…' : 'Save policy'}</button>
          </div>
        </form>}
      </div>
    </main>
  )
}

function PolicySwitch({ checked, description, label, name, onChange }) {
  return <div className="policy-switch-row"><div><label className="fw-semibold" htmlFor={name}>{label}</label><small>{description}</small></div><div className="form-check form-switch"><input checked={checked} className="form-check-input" id={name} name={name} onChange={onChange} role="switch" type="checkbox" /></div></div>
}

function PolicyNumber({ help, label, name, ...props }) {
  return <div className="col-12 col-md-4"><label className="form-label fw-semibold" htmlFor={name}>{label}</label><input className="form-control" id={name} name={name} type="number" {...props} /><div className="form-text">{help}</div></div>
}

function toFormValues(data) {
  return {
    applications_enabled: data.applications_enabled,
    require_verified_documents: data.require_verified_documents,
    minimum_profile_completion: String(data.minimum_profile_completion),
    minimum_cgpa: data.minimum_cgpa ?? '',
    max_active_backlogs: data.max_active_backlogs ?? '',
    student_message: data.student_message || '',
  }
}

function Loading() { return <div className="text-center py-5"><div className="spinner-border text-primary" /></div> }
function formatDateTime(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) }

export default CollegePlacementPolicyPage
