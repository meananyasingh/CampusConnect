import { ArrowRight, BarChart3, Building2, CheckCircle2, GraduationCap, ShieldCheck, Sparkles, UsersRound } from 'lucide-react'
import { Link } from 'react-router-dom'
import PortalCard from '../../components/PortalCard.jsx'

const portals = [
  {
    title: 'Student',
    description: 'Build your career profile, discover eligible opportunities, apply, and track every placement milestone.',
    icon: GraduationCap,
    to: '/student/login',
  },
  {
    title: 'Recruiter',
    description: 'Create your company account, send recruitment requests to colleges, publish opportunities, and manage candidates.',
    icon: Building2,
    to: '/recruiter/login',
  },
  {
    title: 'College Admin',
    description: 'Coordinate placement drives, verify companies, support students, and understand placement outcomes.',
    icon: ShieldCheck,
    to: '/admin-login',
  },
]

function HomePage() {
  return (
    <main className="site-shell">
      <nav className="public-nav container">
        <Link className="brand-lockup" to="/">
          <span className="brand-mark">CC</span>
          <span><strong>CampusConnect</strong><small>Placement, connected.</small></span>
        </Link>
        <a className="btn btn-sm btn-outline-primary" href="#portals">Open your portal</a>
      </nav>
      <section className="hero-section container">
        <div className="row align-items-center g-5">
          <div className="col-12 col-lg-7">
            <span className="hero-pill"><Sparkles size={15} /> Built for modern campus placements</span>
            <h1 className="hero-title mt-4 mb-4">Where campus talent meets the right opportunity.</h1>
            <p className="hero-copy mb-4">One secure workspace for students, recruiting teams, and placement offices—from profile readiness to the final offer.</p>
            <div className="hero-actions">
              <a className="btn btn-primary btn-lg" href="#portals">Get started <ArrowRight size={18} /></a>
              <Link className="btn btn-light btn-lg border" to="/student/login">Student sign in</Link>
            </div>
            <div className="hero-trust-row">
              <span><CheckCircle2 size={17} /> Role-based access</span>
              <span><CheckCircle2 size={17} /> Complete placement journey</span>
              <span><CheckCircle2 size={17} /> College-controlled data</span>
            </div>
          </div>
          <div className="col-12 col-lg-5">
            <div className="hero-workflow-card">
              <div className="hero-workflow-header"><span>Placement workflow</span><i>Live</i></div>
              <WorkflowRow icon={GraduationCap} label="Students build verified profiles" tone="indigo" />
              <WorkflowRow icon={Building2} label="Recruiters publish opportunities" tone="blue" />
              <WorkflowRow icon={ShieldCheck} label="Colleges review and coordinate" tone="green" />
              <div className="hero-outcome"><BarChart3 size={20} /><div><strong>One source of truth</strong><small>Applications, interviews, offers, and reports stay connected.</small></div></div>
            </div>
          </div>
        </div>
      </section>
      <section className="container portal-section" aria-labelledby="portal-heading" id="portals">
        <div className="d-flex align-items-end justify-content-between mb-4">
          <div>
            <p className="eyebrow mb-2">Choose your workspace</p>
            <h2 className="h3 fw-bold mb-0" id="portal-heading">Continue to your portal</h2>
          </div>
          <span className="badge rounded-pill text-bg-light border px-3 py-2">Three connected workspaces</span>
        </div>
        <div className="row g-4">
          {portals.map((portal) => (
            <div className="col-12 col-lg-4" key={portal.title}>
              <PortalCard {...portal} />
            </div>
          ))}
        </div>
      </section>
      <section className="container pb-5">
        <div className="value-strip">
          <div><UsersRound size={22} /><span><strong>Student-first</strong><small>Clear actions and progress at every step</small></span></div>
          <div><Building2 size={22} /><span><strong>Recruiter-ready</strong><small>Manage talent across connected colleges</small></span></div>
          <div><BarChart3 size={22} /><span><strong>Insight-driven</strong><small>Placement outcomes visible in real time</small></span></div>
        </div>
      </section>
      <footer className="public-footer"><div className="container"><span>© {new Date().getFullYear()} CampusConnect</span><span>Built for students, recruiters, and placement teams.</span></div></footer>
    </main>
  )
}

function WorkflowRow({ icon: Icon, label, tone }) {
  return <div className="hero-workflow-row"><span className={tone}><Icon size={19} /></span><strong>{label}</strong><CheckCircle2 className="ms-auto text-success" size={18} /></div>
}

export default HomePage
