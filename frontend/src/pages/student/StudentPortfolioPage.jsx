import {
  ArrowLeft,
  Award,
  BriefcaseBusiness,
  Code2,
  ExternalLink,
  FolderGit2,
  Pencil,
  Plus,
  Trash2,
  X,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { useConfirmDialog } from '../../hooks/useConfirmDialog.js'
import { studentService } from '../../services/studentService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const emptyPortfolio = {
  skills: [],
  projects: [],
  certifications: [],
  experiences: [],
}

const sectionDefinitions = [
  {
    type: 'skills',
    title: 'Skills',
    description: 'Add technical and professional skills recruiters can search for.',
    icon: Code2,
  },
  {
    type: 'projects',
    title: 'Projects',
    description: 'Show practical work, technologies used, and working links.',
    icon: FolderGit2,
  },
  {
    type: 'certifications',
    title: 'Certifications',
    description: 'Record verified courses, credentials, and professional achievements.',
    icon: Award,
  },
  {
    type: 'experiences',
    title: 'Experience',
    description: 'Include internships, jobs, freelance work, and volunteering.',
    icon: BriefcaseBusiness,
  },
]

const formDefinitions = {
  skills: {
    defaults: { skill_name: '', proficiency: 'BEGINNER', years_experience: '0' },
    fields: [
      { name: 'skill_name', label: 'Skill name', required: true, placeholder: 'Django' },
      {
        name: 'proficiency',
        label: 'Proficiency',
        type: 'select',
        required: true,
        options: [
          ['BEGINNER', 'Beginner'],
          ['INTERMEDIATE', 'Intermediate'],
          ['ADVANCED', 'Advanced'],
          ['EXPERT', 'Expert'],
        ],
      },
      { name: 'years_experience', label: 'Years of experience', type: 'number', min: 0, max: 50, step: 0.5, required: true },
    ],
  },
  projects: {
    defaults: { title: '', description: '', technologies: '', github_url: '', live_url: '', start_date: '', end_date: '', is_ongoing: false },
    fields: [
      { name: 'title', label: 'Project title', required: true },
      { name: 'technologies', label: 'Technologies', placeholder: 'Django, React, MySQL' },
      { name: 'description', label: 'Description', type: 'textarea', required: true, full: true },
      { name: 'github_url', label: 'GitHub URL', type: 'url' },
      { name: 'live_url', label: 'Live URL', type: 'url' },
      { name: 'start_date', label: 'Start date', type: 'date', required: true },
      { name: 'end_date', label: 'End date', type: 'date' },
      { name: 'is_ongoing', label: 'This project is ongoing', type: 'checkbox', full: true },
    ],
  },
  certifications: {
    defaults: { name: '', issuing_organization: '', credential_id: '', credential_url: '', issue_date: '', expiry_date: '' },
    fields: [
      { name: 'name', label: 'Certification name', required: true },
      { name: 'issuing_organization', label: 'Issuing organization', required: true },
      { name: 'credential_id', label: 'Credential ID' },
      { name: 'credential_url', label: 'Credential URL', type: 'url' },
      { name: 'issue_date', label: 'Issue date', type: 'date', required: true },
      { name: 'expiry_date', label: 'Expiry date', type: 'date' },
    ],
  },
  experiences: {
    defaults: { organization: '', role: '', employment_type: 'INTERNSHIP', location: '', description: '', start_date: '', end_date: '', is_current: false },
    fields: [
      { name: 'organization', label: 'Organization', required: true },
      { name: 'role', label: 'Role or designation', required: true },
      {
        name: 'employment_type',
        label: 'Employment type',
        type: 'select',
        required: true,
        options: [
          ['INTERNSHIP', 'Internship'],
          ['FULL_TIME', 'Full-time'],
          ['PART_TIME', 'Part-time'],
          ['FREELANCE', 'Freelance'],
          ['VOLUNTEER', 'Volunteer'],
        ],
      },
      { name: 'location', label: 'Location' },
      { name: 'description', label: 'Responsibilities and achievements', type: 'textarea', full: true },
      { name: 'start_date', label: 'Start date', type: 'date', required: true },
      { name: 'end_date', label: 'End date', type: 'date' },
      { name: 'is_current', label: 'I currently work here', type: 'checkbox', full: true },
    ],
  },
}

function StudentPortfolioPage() {
  const confirmAction = useConfirmDialog()
  const [portfolio, setPortfolio] = useState(emptyPortfolio)
  const [loading, setLoading] = useState(true)
  const [editor, setEditor] = useState(null)

  useEffect(() => {
    const loadPortfolio = async () => {
      try {
        setPortfolio(await studentService.getPortfolio())
      } catch (error) {
        toast.error(getApiErrorMessage(error))
      } finally {
        setLoading(false)
      }
    }
    loadPortfolio()
  }, [])

  const saveItem = async (values) => {
    const { type, item } = editor
    try {
      const saved = item
        ? await studentService.updatePortfolioItem(type, item.id, values)
        : await studentService.createPortfolioItem(type, values)
      setPortfolio((current) => ({
        ...current,
        [type]: item
          ? current[type].map((entry) => (entry.id === saved.id ? saved : entry))
          : [saved, ...current[type]],
      }))
      setEditor(null)
      toast.success(item ? 'Portfolio entry updated.' : 'Portfolio entry added.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
      throw error
    }
  }

  const deleteItem = async (type, item) => {
    if (!await confirmAction({ title: 'Delete portfolio entry?', message: 'This entry will be permanently removed from your recruiter-visible portfolio.', confirmLabel: 'Delete entry' })) return
    try {
      await studentService.deletePortfolioItem(type, item.id)
      setPortfolio((current) => ({
        ...current,
        [type]: current[type].filter((entry) => entry.id !== item.id),
      }))
      if (editor?.item?.id === item.id && editor.type === type) setEditor(null)
      toast.success('Portfolio entry deleted.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    }
  }

  return (
    <main className="profile-page">
      <nav className="dashboard-nav">
        <div className="d-flex align-items-center gap-2">
          <span className="brand-mark">CC</span>
          <span className="fw-bold fs-5">CampusConnect</span>
        </div>
        <Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/student/dashboard">
          <ArrowLeft aria-hidden="true" size={17} /> Dashboard
        </Link>
      </nav>

      <div className="container py-5">
        <div className="d-flex flex-wrap align-items-start justify-content-between gap-3 mb-4">
          <div>
            <p className="eyebrow mb-2">Student workspace</p>
            <h1 className="h2 fw-bold mb-2">Career portfolio</h1>
            <p className="text-secondary mb-0">Build the evidence recruiters need to understand your capabilities.</p>
          </div>
          <Link className="btn btn-outline-primary" to="/student/profile">Edit profile and career links</Link>
        </div>

        {loading ? (
          <div className="text-center py-5">
            <div className="spinner-border text-primary" role="status"><span className="visually-hidden">Loading portfolio…</span></div>
          </div>
        ) : (
          <div className="row g-4">
            <div className="col-12 col-xl-8">
              {sectionDefinitions.map((section) => (
                <PortfolioSection
                  key={section.type}
                  {...section}
                  items={portfolio[section.type]}
                  onAdd={() => setEditor({ type: section.type, item: null })}
                  onDelete={(item) => deleteItem(section.type, item)}
                  onEdit={(item) => setEditor({ type: section.type, item })}
                />
              ))}
            </div>

            <div className="col-12 col-xl-4">
              <div className="portfolio-editor-sticky">
                {editor ? (
                  <PortfolioEditor
                    key={`${editor.type}-${editor.item?.id ?? 'new'}`}
                    editor={editor}
                    onCancel={() => setEditor(null)}
                    onSave={saveItem}
                  />
                ) : (
                  <section className="profile-card">
                    <h2 className="h5 fw-bold">Choose what to add</h2>
                    <p className="text-secondary small">Use an Add or Edit button. Your changes are saved through protected Django APIs.</p>
                    <div className="portfolio-summary">
                      {sectionDefinitions.map(({ type, title }) => (
                        <div key={type}><span>{title}</span><strong>{portfolio[type].length}</strong></div>
                      ))}
                    </div>
                  </section>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}

function PortfolioSection({ description, icon: Icon, items, onAdd, onDelete, onEdit, title, type }) {
  return (
    <section className="profile-card mb-4">
      <div className="d-flex align-items-start justify-content-between gap-3 mb-3">
        <div className="d-flex gap-3">
          <span className="portfolio-icon"><Icon aria-hidden="true" size={20} /></span>
          <div>
            <h2 className="h5 fw-bold mb-1">{title}</h2>
            <p className="text-secondary small mb-0">{description}</p>
          </div>
        </div>
        <button className="btn btn-sm btn-primary d-flex align-items-center gap-1" onClick={onAdd} type="button">
          <Plus aria-hidden="true" size={16} /> Add
        </button>
      </div>
      {items.length ? (
        <div className={type === 'skills' ? 'skill-grid' : 'd-grid gap-3'}>
          {items.map((item) => (
            <PortfolioItem key={item.id} item={item} onDelete={onDelete} onEdit={onEdit} type={type} />
          ))}
        </div>
      ) : (
        <div className="portfolio-empty">No {title.toLowerCase()} added yet.</div>
      )}
    </section>
  )
}

function PortfolioItem({ item, onDelete, onEdit, type }) {
  if (type === 'skills') {
    return (
      <article className="skill-card">
        <div><strong>{item.skill_name}</strong><small>{item.proficiency_display} · {item.years_experience} years</small></div>
        <ItemActions item={item} onDelete={onDelete} onEdit={onEdit} />
      </article>
    )
  }

  const content = {
    projects: {
      title: item.title,
      subtitle: item.technologies,
      period: formatPeriod(item.start_date, item.end_date, item.is_ongoing),
      description: item.description,
      links: [['GitHub', item.github_url], ['Live project', item.live_url]],
    },
    certifications: {
      title: item.name,
      subtitle: item.issuing_organization,
      period: `Issued ${formatDate(item.issue_date)}${item.expiry_date ? ` · Expires ${formatDate(item.expiry_date)}` : ''}`,
      description: item.credential_id ? `Credential ID: ${item.credential_id}` : '',
      links: [['View credential', item.credential_url]],
    },
    experiences: {
      title: item.role,
      subtitle: `${item.organization} · ${item.employment_type_display}${item.location ? ` · ${item.location}` : ''}`,
      period: formatPeriod(item.start_date, item.end_date, item.is_current),
      description: item.description,
      links: [],
    },
  }[type]

  return (
    <article className="portfolio-entry">
      <div className="d-flex justify-content-between gap-3">
        <div>
          <h3 className="h6 fw-bold mb-1">{content.title}</h3>
          {content.subtitle && <p className="text-secondary small mb-1">{content.subtitle}</p>}
          <p className="portfolio-period mb-0">{content.period}</p>
        </div>
        <ItemActions item={item} onDelete={onDelete} onEdit={onEdit} />
      </div>
      {content.description && <p className="small mt-3 mb-2 portfolio-description">{content.description}</p>}
      <div className="d-flex flex-wrap gap-3">
        {content.links.filter(([, url]) => url).map(([label, url]) => (
          <a className="portfolio-link" href={url} key={label} rel="noreferrer" target="_blank">
            {label} <ExternalLink aria-hidden="true" size={13} />
          </a>
        ))}
      </div>
    </article>
  )
}

function ItemActions({ item, onDelete, onEdit }) {
  return (
    <div className="d-flex gap-1">
      <button aria-label="Edit entry" className="btn btn-sm btn-light" onClick={() => onEdit(item)} title="Edit" type="button">
        <Pencil aria-hidden="true" size={15} />
      </button>
      <button aria-label="Delete entry" className="btn btn-sm btn-light text-danger" onClick={() => onDelete(item)} title="Delete" type="button">
        <Trash2 aria-hidden="true" size={15} />
      </button>
    </div>
  )
}

function PortfolioEditor({ editor, onCancel, onSave }) {
  const definition = formDefinitions[editor.type]
  const [values, setValues] = useState({ ...definition.defaults, ...(editor.item ?? {}) })
  const [saving, setSaving] = useState(false)
  const section = sectionDefinitions.find(({ type }) => type === editor.type)

  const updateValue = (event) => {
    const { checked, name, type, value } = event.target
    setValues((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
  }

  const submit = async (event) => {
    event.preventDefault()
    setSaving(true)
    const payload = { ...values }
    delete payload.id
    delete payload.created_at
    delete payload.updated_at
    delete payload.proficiency_display
    delete payload.employment_type_display
    if (payload.is_ongoing) payload.end_date = null
    if (payload.is_current) payload.end_date = null
    Object.keys(payload).forEach((key) => {
      if (payload[key] === '' && ['end_date', 'expiry_date'].includes(key)) payload[key] = null
    })
    try {
      await onSave(payload)
    } catch {
      setSaving(false)
    }
  }

  return (
    <section className="profile-card">
      <div className="d-flex align-items-start justify-content-between gap-3 mb-3">
        <div>
          <p className="eyebrow mb-1">{editor.item ? 'Edit entry' : 'New entry'}</p>
          <h2 className="h5 fw-bold mb-0">{section.title}</h2>
        </div>
        <button aria-label="Close editor" className="btn btn-sm btn-light" onClick={onCancel} type="button"><X size={17} /></button>
      </div>
      <form onSubmit={submit}>
        <div className="row g-3">
          {definition.fields.map((field) => (
            <PortfolioField field={field} key={field.name} onChange={updateValue} values={values} />
          ))}
        </div>
        <div className="d-flex gap-2 mt-4">
          <button className="btn btn-primary flex-grow-1" disabled={saving} type="submit">{saving ? 'Saving…' : 'Save entry'}</button>
          <button className="btn btn-outline-secondary" disabled={saving} onClick={onCancel} type="button">Cancel</button>
        </div>
      </form>
    </section>
  )
}

function PortfolioField({ field, onChange, values }) {
  const inputId = `portfolio-${field.name}`
  if (field.type === 'checkbox') {
    return (
      <div className="col-12">
        <div className="form-check">
          <input checked={Boolean(values[field.name])} className="form-check-input" id={inputId} name={field.name} onChange={onChange} type="checkbox" />
          <label className="form-check-label" htmlFor={inputId}>{field.label}</label>
        </div>
      </div>
    )
  }

  const fieldProps = {
    className: 'form-control',
    id: inputId,
    name: field.name,
    onChange,
    placeholder: field.placeholder,
    required: field.required,
    value: values[field.name] ?? '',
  }
  return (
    <div className={field.full ? 'col-12' : 'col-12 col-md-6 col-xl-12'}>
      <label className="form-label fw-semibold small" htmlFor={inputId}>{field.label}</label>
      {field.type === 'textarea' ? (
        <textarea {...fieldProps} maxLength="2000" rows="4" />
      ) : field.type === 'select' ? (
        <select {...fieldProps}>{field.options.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
      ) : (
        <input {...fieldProps} max={field.max} min={field.min} step={field.step} type={field.type ?? 'text'} />
      )}
    </div>
  )
}

function formatDate(value) {
  if (!value) return 'Present'
  return new Intl.DateTimeFormat('en-IN', { month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`))
}

function formatPeriod(start, end, current) {
  return `${formatDate(start)} – ${current ? 'Present' : formatDate(end)}`
}

export default StudentPortfolioPage
