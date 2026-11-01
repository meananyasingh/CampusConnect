import { LogOut } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../../hooks/useAuth.js'
import NotificationBell from '../../components/NotificationBell.jsx'

const loginPaths = {
  STUDENT: '/student/login',
  RECRUITER: '/recruiter/login',
  ADMIN: '/admin-login',
}

function DashboardPlaceholder({ title }) {
  const [signingOut, setSigningOut] = useState(false)
  const { logout, user } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    setSigningOut(true)
    await logout()
    navigate(loginPaths[user.role], { replace: true })
  }

  return (
    <main className="dashboard-shell">
      <nav className="dashboard-nav">
        <div className="d-flex align-items-center gap-2">
          <span className="brand-mark">CC</span>
          <span className="fw-bold fs-5">CampusConnect</span>
        </div>
        <div className="d-flex align-items-center gap-2"><NotificationBell /><button className="btn btn-outline-secondary d-flex align-items-center gap-2" disabled={signingOut} onClick={handleLogout} type="button">
          <LogOut aria-hidden="true" size={17} /> Sign out
        </button></div>
      </nav>
      <section className="container py-5">
        <p className="eyebrow mb-2">Authenticated workspace</p>
        <h1 className="display-6 fw-bold mb-3">{title}</h1>
        <p className="text-secondary fs-5">
          Signed in as {user.first_name || user.email}. The secure dashboard route is ready; domain features come next.
        </p>
        <div className="alert alert-primary mt-4" role="status">
          Your Django-issued JWT was accepted and your role was verified before this page rendered.
        </div>
        {user.role === 'STUDENT' && (
          <div className="d-flex flex-wrap gap-2 mt-2">
            <Link className="btn btn-primary" to="/student/profile">Complete your profile</Link>
            <Link className="btn btn-outline-primary" to="/student/portfolio">Build career portfolio</Link>
            <Link className="btn btn-outline-primary" to="/student/resumes">Manage resumes</Link>
            <Link className="btn btn-outline-primary" to="/student/opportunities">Browse opportunities</Link>
            <Link className="btn btn-outline-primary" to="/student/applications">Track applications</Link>
            <Link className="btn btn-outline-primary" to="/student/interviews">View interviews</Link>
            <Link className="btn btn-outline-primary" to="/student/placements">Placement offers</Link>
          </div>
        )}
        {user.role === 'RECRUITER' && (
          <div className="d-flex flex-wrap gap-2 mt-2"><Link className="btn btn-primary" to="/recruiter/company">Manage company profile</Link><Link className="btn btn-outline-primary" to="/recruiter/opportunities">Manage opportunities</Link><Link className="btn btn-outline-primary" to="/recruiter/applications">Review applicants</Link></div>
        )}
        {user.role === 'ADMIN' && (
          <Link className="btn btn-primary mt-2" to="/admin/companies">Review company requests</Link>
        )}
      </section>
    </main>
  )
}

export default DashboardPlaceholder
