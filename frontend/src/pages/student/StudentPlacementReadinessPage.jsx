import { ArrowLeft, CheckCircle2, FileCheck2, ShieldCheck, UserRoundCheck, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { placementService } from '../../services/placementService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

function StudentPlacementReadinessPage() {
  const [readiness, setReadiness] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    placementService.getStudentReadiness()
      .then(setReadiness)
      .catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  return (
    <main className="profile-page">
      <nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/student/dashboard"><ArrowLeft size={17} /> Dashboard</Link></nav>
      <div className="container py-5 policy-page-width">
        <div className="mb-4"><p className="eyebrow mb-2">Before you apply</p><h1 className="h2 fw-bold mb-2">Placement readiness</h1><p className="text-secondary mb-0">See your college-wide placement requirements and resolve any pending items.</p></div>
        {loading ? <Loading /> : readiness && <>
          <section className={`readiness-hero ${readiness.is_ready ? 'ready' : 'action-needed'}`}>
            <span>{readiness.is_ready ? <CheckCircle2 size={28} /> : <ShieldCheck size={28} />}</span>
            <div><p>{readiness.is_ready ? 'Ready to apply' : 'Action needed before applying'}</p><h2>{readiness.is_ready ? 'You meet your college placement policy.' : `${readiness.blockers.length} requirement${readiness.blockers.length === 1 ? '' : 's'} still pending.`}</h2><small>Individual companies may set additional eligibility rules for their opportunities.</small></div>
          </section>
          {readiness.policy.student_message && <div className="alert alert-info mt-4 mb-0"><strong>Message from your placement office:</strong> {readiness.policy.student_message}</div>}
          {!readiness.is_ready && <section className="profile-card mt-4"><h2 className="h5 fw-bold mb-3">What you need to complete</h2><ul className="readiness-blockers mb-0">{readiness.blockers.map((blocker) => <li key={blocker}><XCircle size={18} /> <span>{blocker}</span></li>)}</ul></section>}
          <div className="row g-4 mt-0">
            <ReadinessCard action="Update profile" icon={UserRoundCheck} label="Profile completion" ready={readiness.profile_completion >= readiness.policy.minimum_profile_completion} to="/student/profile" value={`${readiness.profile_completion}%`}><span>College minimum: {readiness.policy.minimum_profile_completion}%</span></ReadinessCard>
            <ReadinessCard action="Manage documents" icon={FileCheck2} label="Required documents" ready={!readiness.policy.require_verified_documents || readiness.document_verification.is_complete} to="/student/documents" value={`${readiness.document_verification.verified_required}/${readiness.document_verification.required_total}`}><span>{readiness.policy.require_verified_documents ? 'Verification required' : 'Not required to apply'}</span></ReadinessCard>
          </div>
          <section className="profile-card mt-4">
            <h2 className="h5 fw-bold mb-3">College application rules</h2>
            <div className="policy-rule-grid"><PolicyRule active={readiness.policy.applications_enabled} label="Applications" value={readiness.policy.applications_enabled ? 'Open' : 'Paused'} /><PolicyRule active label="Minimum CGPA" value={readiness.policy.minimum_cgpa ?? 'No college minimum'} /><PolicyRule active label="Maximum active backlogs" value={readiness.policy.max_active_backlogs ?? 'No college limit'} /></div>
          </section>
          <section className="profile-card mt-4">
            <div className="d-flex justify-content-between align-items-center gap-3 mb-3"><h2 className="h5 fw-bold mb-0">Document checklist</h2><Link to="/student/documents">Manage documents</Link></div>
            <div className="readiness-document-list">{readiness.document_verification.requirements.map((item) => <div key={item.key}><span className={item.is_verified ? 'verified' : ''}>{item.is_verified ? <CheckCircle2 size={18} /> : <XCircle size={18} />}</span><strong>{item.label}</strong><small>{item.status === 'VERIFIED' ? 'Verified' : item.status === 'PENDING' ? 'Awaiting college review' : 'Not uploaded'}</small></div>)}</div>
          </section>
        </>}
      </div>
    </main>
  )
}

function ReadinessCard({ action, children, icon: Icon, label, ready, to, value }) {
  return <div className="col-12 col-md-6"><article className="profile-card readiness-card h-100"><div><span className={ready ? 'ready-icon' : 'pending-icon'}><Icon size={21} /></span><div><small>{label}</small><strong>{value}</strong>{children}</div></div><Link className="btn btn-sm btn-outline-primary" to={to}>{action}</Link></article></div>
}

function PolicyRule({ active, label, value }) { return <div><span className={active ? 'ready-icon' : 'pending-icon'}>{active ? <CheckCircle2 size={17} /> : <XCircle size={17} />}</span><p><small>{label}</small><strong>{value}</strong></p></div> }
function Loading() { return <div className="text-center py-5"><div className="spinner-border text-primary" /></div> }

export default StudentPlacementReadinessPage
