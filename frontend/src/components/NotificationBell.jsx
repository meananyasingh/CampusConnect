import { Bell } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { notificationService } from '../services/notificationService.js'

function NotificationBell() {
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    notificationService.unreadCount().then(setUnreadCount).catch(() => {})
  }, [])

  return (
    <Link aria-label={`${unreadCount} unread notifications`} className="notification-bell" to="/notifications">
      <Bell aria-hidden="true" size={20} />
      {unreadCount > 0 && <span>{unreadCount > 99 ? '99+' : unreadCount}</span>}
    </Link>
  )
}

export default NotificationBell
