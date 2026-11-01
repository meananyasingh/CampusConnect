import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

function PortalCard({ description, icon: Icon, title, to }) {
  return (
    <article className="portal-card d-flex flex-column">
      <span className="portal-icon mb-4">
        <Icon aria-hidden="true" size={23} strokeWidth={2} />
      </span>
      <h2 className="h4 fw-bold text-dark">{title}</h2>
      <p className="text-secondary lh-lg flex-grow-1">{description}</p>
      <Link className="portal-link mt-2" to={to}>
        Open portal <ArrowRight aria-hidden="true" size={17} />
      </Link>
    </article>
  )
}

export default PortalCard
