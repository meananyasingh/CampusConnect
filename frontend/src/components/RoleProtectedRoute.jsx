import { Navigate, useLocation } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth.js'

const loginRoutes = {
  STUDENT: '/student/login',
  RECRUITER: '/recruiter/login',
  ADMIN: '/admin-login',
}

const dashboardRoutes = {
  STUDENT: '/student/dashboard',
  RECRUITER: '/recruiter/dashboard',
  ADMIN: '/admin-dashboard',
}

function RoleProtectedRoute({ children, role }) {
  const { initializing, isAuthenticated, user } = useAuth()
  const location = useLocation()

  if (initializing) {
    return (
      <main className="site-shell d-flex align-items-center justify-content-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Checking your session…</span>
        </div>
      </main>
    )
  }

  if (!isAuthenticated) {
    return <Navigate replace state={{ from: location }} to={role ? loginRoutes[role] : '/'} />
  }

  if (role && user.role !== role) {
    return <Navigate replace to={dashboardRoutes[user.role]} />
  }

  return children
}

export default RoleProtectedRoute
