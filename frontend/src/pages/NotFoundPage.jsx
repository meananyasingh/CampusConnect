import { Link } from 'react-router-dom'

function NotFoundPage() {
  return (
    <main className="site-shell d-flex align-items-center justify-content-center p-3">
      <section className="placeholder-panel text-center">
        <p className="eyebrow mb-2">404</p>
        <h1 className="h2 fw-bold mb-3">Page not found</h1>
        <p className="text-secondary mb-4">The page you requested is not part of CampusConnect.</p>
        <Link className="btn btn-primary" to="/">Return home</Link>
      </section>
    </main>
  )
}

export default NotFoundPage
