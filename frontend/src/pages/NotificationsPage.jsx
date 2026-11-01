import { ArrowLeft, Bell, BriefcaseBusiness, Building2, CalendarClock, CheckCheck, Megaphone, Settings2, Trophy } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth.js'
import { notificationService } from '../services/notificationService.js'
import { getApiErrorMessage } from '../utils/apiErrors.js'

const dashboardPaths = { STUDENT: '/student/dashboard', RECRUITER: '/recruiter/dashboard', ADMIN: '/admin-dashboard' }
const categoryIcons = { COMPANY: Building2, APPLICATION: BriefcaseBusiness, INTERVIEW: CalendarClock, PLACEMENT: Trophy, ANNOUNCEMENT: Megaphone, SYSTEM: Bell }

function NotificationsPage() {
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [preferences, setPreferences] = useState(null)
  const [showPreferences, setShowPreferences] = useState(false)
  const [savingPreferences, setSavingPreferences] = useState(false)
  const { user } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    Promise.all([notificationService.list(), notificationService.getPreferences()])
      .then(([items, preferenceData]) => { setNotifications(items); setPreferences(preferenceData) })
      .catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  const openNotification = async (notification) => {
    try {
      if (!notification.is_read) {
        const updated = await notificationService.markRead(notification.id)
        setNotifications((current) => current.map((item) => item.id === updated.id ? updated : item))
      }
      if (notification.link) navigate(notification.link)
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    }
  }

  const markAllRead = async () => {
    try {
      await notificationService.markAllRead()
      setNotifications((current) => current.map((item) => ({ ...item, is_read: true })))
      toast.success('All notifications marked as read.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    }
  }

  const hasUnread = notifications.some((notification) => !notification.is_read)

  const savePreferences = async () => {
    setSavingPreferences(true)
    try {
      setPreferences(await notificationService.updatePreferences(preferences))
      toast.success('Email preferences updated.')
    } catch (error) { toast.error(getApiErrorMessage(error)) } finally { setSavingPreferences(false) }
  }

  return (
    <main className="profile-page">
      <nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to={dashboardPaths[user.role]}><ArrowLeft size={17} /> Dashboard</Link></nav>
      <div className="container py-5"><div className="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4"><div><p className="eyebrow mb-2">Activity centre</p><h1 className="h2 fw-bold mb-2">Notifications</h1><p className="text-secondary mb-0">Important updates from your CampusConnect workflows.</p></div><div className="d-flex flex-wrap gap-2"><button className="btn btn-outline-secondary d-flex align-items-center gap-2" onClick={() => setShowPreferences((value) => !value)} type="button"><Settings2 size={17} /> Email preferences</button>{hasUnread && <button className="btn btn-outline-primary d-flex align-items-center gap-2" onClick={markAllRead} type="button"><CheckCheck size={17} /> Mark all as read</button>}</div></div>{showPreferences && preferences && <PreferencePanel onChange={setPreferences} onSave={savePreferences} preferences={preferences} saving={savingPreferences} />}{loading ? <div className="text-center py-5"><div className="spinner-border text-primary" /></div> : notifications.length ? <section className="profile-card notification-list">{notifications.map((notification) => <NotificationItem key={notification.id} notification={notification} onOpen={() => openNotification(notification)} />)}</section> : <div className="profile-card portfolio-empty">You have no notifications yet.</div>}</div>
    </main>
  )
}

function NotificationItem({ notification, onOpen }) {
  const Icon = categoryIcons[notification.category] || Bell
  return <button className={`notification-item ${notification.is_read ? '' : 'notification-unread'}`} onClick={onOpen} type="button"><span className="portfolio-icon"><Icon size={19} /></span><span className="notification-copy"><span><strong>{notification.title}</strong>{!notification.is_read && <i>New</i>}</span><small>{notification.message}</small><time>{formatTime(notification.created_at)}</time></span></button>
}

function PreferencePanel({ onChange, onSave, preferences, saving }) {
  const options = [
    ['email_company', 'Company and college requests'],
    ['email_applications', 'Application status updates'],
    ['email_interviews', 'Interview schedules and results'],
    ['email_placements', 'Placement offers and decisions'],
    ['email_announcements', 'College announcements'],
    ['email_system', 'Documents and system updates'],
  ]
  return <section className="profile-card notification-preferences mb-4"><div className="d-flex flex-wrap justify-content-between gap-3 mb-3"><div><h2 className="h5 fw-bold mb-1">Email preferences</h2><p className="small text-secondary mb-0">In-app notifications remain available even when an email category is disabled.</p></div><div className="form-check form-switch"><input checked={preferences.email_enabled} className="form-check-input" id="email-enabled" onChange={(event) => onChange((current) => ({ ...current, email_enabled: event.target.checked }))} role="switch" type="checkbox" /><label className="form-check-label fw-semibold" htmlFor="email-enabled">Email notifications</label></div></div><div className="notification-preference-grid">{options.map(([field, label]) => <label className={!preferences.email_enabled ? 'disabled' : ''} key={field}><input checked={preferences[field]} disabled={!preferences.email_enabled} onChange={(event) => onChange((current) => ({ ...current, [field]: event.target.checked }))} type="checkbox" /><span>{label}</span></label>)}</div><div className="text-end mt-3"><button className="btn btn-primary" disabled={saving} onClick={onSave} type="button">{saving ? 'Saving…' : 'Save email preferences'}</button></div></section>
}

function formatTime(value) { return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) }

export default NotificationsPage
