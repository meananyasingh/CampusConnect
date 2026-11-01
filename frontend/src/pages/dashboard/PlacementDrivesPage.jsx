import { ArrowLeft, Building2, CalendarDays, FileCheck2, MapPin, UserRoundCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { placementService } from '../../services/placementService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const roleConfig = {
  STUDENT: { eyebrow: 'Campus hiring calendar', title: 'Placement drives', description: 'Explore coordinated recruitment events published by your college.', back: '/student/dashboard', opportunityPath: '/student/opportunities' },
  RECRUITER: { eyebrow: 'College hiring calendar', title: 'Company placement drives', description: 'Track college drives containing opportunities from your company.', back: '/recruiter/dashboard', opportunityPath: '/recruiter/opportunities' },
}

function PlacementDrivesPage({ role }) {
  const [drives, setDrives] = useState([])
  const [loading, setLoading] = useState(true)
  const config = roleConfig[role]
  useEffect(() => {
    const request = role === 'STUDENT' ? placementService.listStudentDrives : placementService.listRecruiterDrives
    request().then(setDrives).catch((error) => toast.error(getApiErrorMessage(error))).finally(() => setLoading(false))
  }, [role])
  return <main className="profile-page"><nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to={config.back}><ArrowLeft size={17} /> Dashboard</Link></nav><div className="container py-5"><div className="mb-4"><p className="eyebrow mb-2">{config.eyebrow}</p><h1 className="h2 fw-bold mb-2">{config.title}</h1><p className="text-secondary mb-0">{config.description}</p></div>{loading ? <div className="text-center py-5"><div className="spinner-border text-primary" /></div> : drives.length ? <div className="d-grid gap-4">{drives.map((drive) => <article className="profile-card" key={drive.id}><div className="d-flex flex-wrap justify-content-between gap-3"><div><span className={`application-status status-${drive.status.toLowerCase()}`}>{drive.status_display}</span><h2 className="h4 fw-bold mt-2 mb-1">{drive.title}</h2><p className="text-secondary small mb-0"><CalendarDays size={15} /> {formatDate(drive.start_date)} – {formatDate(drive.end_date)}{drive.venue && <> · <MapPin size={15} /> {drive.venue}</>}</p></div><span className="badge text-bg-primary-subtle align-self-start">{drive.college.name}</span></div>{drive.description && <p className="portfolio-description mt-3">{drive.description}</p>}<div className="drive-metrics"><span><Building2 size={17} /><strong>{drive.company_count}</strong> companies</span><span><FileCheck2 size={17} /><strong>{drive.opportunity_count}</strong> opportunities</span><span><UserRoundCheck size={17} /><strong>{drive.selected_count}</strong> selected</span></div><div className="drive-opportunities">{drive.opportunities.map((item) => <span key={item.id}><strong>{item.company.name}</strong>{item.title}</span>)}</div><Link className="btn btn-sm btn-outline-primary mt-3" to={config.opportunityPath}>{role === 'STUDENT' ? 'View opportunities' : 'Manage opportunities'}</Link></article>)}</div> : <div className="profile-card portfolio-empty">No placement drives are available yet.</div>}</div></main>
}
function formatDate(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`)) }
export default PlacementDrivesPage
