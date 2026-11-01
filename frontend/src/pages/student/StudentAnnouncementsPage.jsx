import { ArrowLeft, BellRing, BriefcaseBusiness, CalendarDays, Check, Clock3, Pin } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { announcementService } from '../../services/announcementService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

function StudentAnnouncementsPage() {
  const [announcements, setAnnouncements] = useState([])
  const [loading, setLoading] = useState(true)
  useEffect(() => { announcementService.listStudent().then(setAnnouncements).catch((error) => toast.error(getApiErrorMessage(error))).finally(() => setLoading(false)) }, [])
  const markRead = async (item) => {
    if (item.is_read) return
    try { const updated = await announcementService.markRead(item.id); setAnnouncements((current) => current.map((entry) => entry.id === updated.id ? updated : entry)) } catch (error) { toast.error(getApiErrorMessage(error)) }
  }
  return <main className="profile-page"><nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/student/dashboard"><ArrowLeft size={17} /> Dashboard</Link></nav><div className="container py-5"><div className="mb-4"><p className="eyebrow mb-2">College communication</p><h1 className="h2 fw-bold mb-2">Announcements</h1><p className="text-secondary mb-0">Placement notices selected for your program and graduation year.</p></div>{loading ? <Loading /> : announcements.length ? <div className="d-grid gap-3">{announcements.map((item) => <AnnouncementCard item={item} key={item.id} onRead={() => markRead(item)} />)}</div> : <div className="profile-card portfolio-empty">No current announcements for you.</div>}</div></main>
}

function AnnouncementCard({ item, onRead }) {
  const relatedPath = item.related_drive ? '/student/drives' : item.related_opportunity ? '/student/opportunities' : null
  return <article className={`profile-card announcement-card priority-${item.priority.toLowerCase()} ${item.is_read ? '' : 'announcement-new'}`} onClick={onRead}><div className="d-flex flex-wrap justify-content-between gap-3"><div className="d-flex gap-3"><span className="portfolio-icon"><BellRing size={19} /></span><div><div className="d-flex flex-wrap gap-2 mb-1">{item.is_pinned && <span className="badge text-bg-primary-subtle"><Pin size={12} /> Pinned</span>}<span className="badge text-bg-light">{item.announcement_type_display}</span>{!item.is_read && <span className="badge text-bg-primary">New</span>}</div><h2 className="h5 fw-bold mb-1">{item.title}</h2><small className="text-secondary">{item.company?.name || item.college.name} · {formatDateTime(item.publish_at)}</small></div></div><span className={`announcement-priority ${item.priority.toLowerCase()}`}>{item.priority_display}</span></div><p className="portfolio-description mt-3 mb-0">{item.body}</p><div className="d-flex flex-wrap gap-3 mt-3 small text-secondary"><span><Clock3 size={14} /> {item.expires_at ? `Available until ${formatDateTime(item.expires_at)}` : 'No expiry'}</span>{item.related_drive && <span><CalendarDays size={14} /> {item.related_drive.title}</span>}{item.related_opportunity && <span><BriefcaseBusiness size={14} /> {item.related_opportunity.title}</span>}</div><div className="d-flex gap-2 mt-3">{relatedPath && <Link className="btn btn-sm btn-outline-primary" onClick={onRead} to={relatedPath}>View related {item.related_drive ? 'drive' : 'opportunity'}</Link>}{!item.is_read && <button className="btn btn-sm btn-light d-flex align-items-center gap-1" onClick={(event) => { event.stopPropagation(); onRead() }} type="button"><Check size={14} /> Mark read</button>}</div></article>
}
function Loading() { return <div className="text-center py-5"><div className="spinner-border text-primary" /></div> }
function formatDateTime(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) }
export default StudentAnnouncementsPage
