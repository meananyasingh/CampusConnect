import { ArrowUpRight } from 'lucide-react'
import { Link } from 'react-router-dom'

function PortalActionGrid({ items, label = 'Quick access' }) {
  return (
    <section className="portal-action-section mb-4" aria-label={label}>
      <div className="portal-action-heading">
        <div>
          <p className="eyebrow mb-1">{label}</p>
          <h2>What would you like to do?</h2>
        </div>
        <span>{items.length} tools</span>
      </div>
      <div className="portal-action-grid">
        {items.map(({ description, icon: Icon, title, to }) => (
          <Link className="portal-action-card" key={to} to={to}>
            <span><Icon aria-hidden="true" size={20} /></span>
            <div>
              <strong>{title}</strong>
              <small>{description}</small>
            </div>
            <ArrowUpRight aria-hidden="true" className="portal-action-arrow" size={17} />
          </Link>
        ))}
      </div>
    </section>
  )
}

export default PortalActionGrid
