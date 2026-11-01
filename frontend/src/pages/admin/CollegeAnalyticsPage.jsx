import { ArrowLeft, Download, FileSpreadsheet } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { analyticsService } from '../../services/analyticsService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const chartColors = ['#4f46e5', '#0284c7', '#059669', '#d97706', '#dc2626', '#7c3aed', '#64748b']

function CollegeAnalyticsPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState('')

  useEffect(() => {
    analyticsService.overview()
      .then(setData)
      .catch((error) => toast.error(getApiErrorMessage(error)))
      .finally(() => setLoading(false))
  }, [])

  const download = async (type) => {
    setDownloading(type)
    try {
      await analyticsService.downloadReport(type)
      toast.success(`${type[0].toUpperCase()}${type.slice(1)} report downloaded.`)
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setDownloading('')
    }
  }

  return <main className="profile-page"><nav className="dashboard-nav"><div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div><Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/admin-dashboard"><ArrowLeft size={17} /> Dashboard</Link></nav><div className="container py-5"><div className="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4"><div><p className="eyebrow mb-2">Placement intelligence</p><h1 className="h2 fw-bold mb-2">Analytics and reports</h1><p className="text-secondary mb-0">Understand application progress and placement performance across your college.</p></div><div className="d-flex flex-wrap gap-2">{['students', 'applications', 'placements'].map((type) => <button className="btn btn-outline-primary btn-sm d-flex align-items-center gap-2" disabled={Boolean(downloading)} key={type} onClick={() => download(type)} type="button"><Download size={15} /> {downloading === type ? 'Downloading…' : `${type[0].toUpperCase()}${type.slice(1)} CSV`}</button>)}</div></div>{loading ? <div className="text-center py-5"><div className="spinner-border text-primary" /></div> : data && <><div className="row g-4"><div className="col-12 col-xl-6"><ChartCard title="Application pipeline">{hasCounts(data.application_pipeline) ? <ResponsiveContainer height={310} width="100%"><PieChart><Pie data={data.application_pipeline.filter((item) => item.count)} dataKey="count" nameKey="name" outerRadius={105}>{data.application_pipeline.filter((item) => item.count).map((item, index) => <Cell fill={chartColors[index % chartColors.length]} key={item.name} />)}</Pie><Tooltip /><Legend /></PieChart></ResponsiveContainer> : <EmptyChart />}</ChartCard></div><div className="col-12 col-xl-6"><ChartCard title="Monthly applications">{data.monthly_applications.length ? <ResponsiveContainer height={310} width="100%"><LineChart data={data.monthly_applications}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="month" tickFormatter={monthLabel} /><YAxis allowDecimals={false} /><Tooltip labelFormatter={monthLabel} /><Line dataKey="applications" stroke="#4f46e5" strokeWidth={3} type="monotone" /></LineChart></ResponsiveContainer> : <EmptyChart />}</ChartCard></div><div className="col-12"><ChartCard title="Branch-wise placement performance">{data.branch_performance.length ? <ResponsiveContainer height={340} width="100%"><BarChart data={data.branch_performance} margin={{ bottom: 70 }}><CartesianGrid strokeDasharray="3 3" /><XAxis angle={-25} dataKey="name" height={90} textAnchor="end" /><YAxis allowDecimals={false} /><Tooltip /><Legend /><Bar dataKey="total_students" fill="#94a3b8" name="Total students" /><Bar dataKey="placed_students" fill="#4f46e5" name="Placed students" /></BarChart></ResponsiveContainer> : <EmptyChart />}</ChartCard></div><div className="col-12"><section className="profile-card"><h2 className="h5 fw-bold mb-3">Company placement performance</h2>{data.company_placements.length ? <div className="table-responsive"><table className="table align-middle mb-0"><thead><tr><th>Company</th><th>Placed students</th><th>Average package</th><th>Highest package</th></tr></thead><tbody>{data.company_placements.map((company) => <tr key={company.name}><td className="fw-semibold">{company.name}</td><td>{company.placed_students}</td><td>{formatPackage(company.average_package)}</td><td>{formatPackage(company.highest_package)}</td></tr>)}</tbody></table></div> : <div className="portfolio-empty"><FileSpreadsheet size={22} className="mb-2" /><br />Company statistics will appear after placements are recorded.</div>}</section></div></div></>}</div></main>
}

function ChartCard({ children, title }) { return <section className="profile-card h-100"><h2 className="h5 fw-bold mb-3">{title}</h2>{children}</section> }
function EmptyChart() { return <div className="portfolio-empty py-5">No data is available for this chart yet.</div> }
function hasCounts(items) { return items.some((item) => item.count > 0) }
function monthLabel(value) { return new Intl.DateTimeFormat('en-IN', { month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`)) }
function formatPackage(value) { return value == null ? '—' : new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value)) }

export default CollegeAnalyticsPage
