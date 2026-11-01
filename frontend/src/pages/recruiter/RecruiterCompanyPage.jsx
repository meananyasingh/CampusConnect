import { ArrowLeft, Building2, Camera, Plus, Save, ShieldCheck, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { useConfirmDialog } from '../../hooks/useConfirmDialog.js'
import { useAuth } from '../../hooks/useAuth.js'
import { companyService } from '../../services/companyService.js'
import { collegeService } from '../../services/collegeService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const companyFields = [
  'name', 'industry', 'website', 'contact_email', 'phone', 'headquarters',
  'company_size', 'description', 'linkedin_url',
]

function RecruiterCompanyPage() {
  const confirmAction = useConfirmDialog()
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [colleges, setColleges] = useState([])
  const [selectedCollege, setSelectedCollege] = useState('')
  const [requesting, setRequesting] = useState(false)
  const { updateCurrentUser } = useAuth()
  const { register, handleSubmit, reset, formState: { errors } } = useForm()

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const [data, collegeData] = await Promise.all([
          companyService.getRecruiterProfile(),
          collegeService.list(),
        ])
        setProfile(data)
        setColleges(collegeData)
        reset({
          first_name: data.user.first_name,
          last_name: data.user.last_name,
          designation: data.designation,
          recruiter_phone: data.phone,
          ...Object.fromEntries(companyFields.map((field) => [field, data.company[field] ?? ''])),
        })
      } catch (error) {
        toast.error(getApiErrorMessage(error))
      } finally {
        setLoading(false)
      }
    }
    loadProfile()
  }, [reset])

  const requestCollege = async () => {
    if (!selectedCollege) return
    setRequesting(true)
    try {
      const partnership = await companyService.requestCollegeAccess(selectedCollege)
      setProfile((current) => ({
        ...current,
        company: {
          ...current.company,
          partnerships: [partnership, ...current.company.partnerships],
        },
      }))
      setSelectedCollege('')
      toast.success(`Recruitment request sent to ${partnership.college.name}. The college will review and respond.`)
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setRequesting(false)
    }
  }

  const cancelRequest = async (partnership) => {
    if (!await confirmAction({ title: 'Cancel college request?', message: `The pending recruitment request to ${partnership.college.name} will be withdrawn.`, confirmLabel: 'Cancel request' })) return
    try {
      await companyService.cancelCollegeRequest(partnership.id)
      setProfile((current) => ({
        ...current,
        company: {
          ...current.company,
          partnerships: current.company.partnerships.filter((item) => item.id !== partnership.id),
        },
      }))
      toast.success('College request cancelled.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    }
  }

  const saveProfile = async (values) => {
    setSaving(true)
    try {
      const updatedProfile = await companyService.updateRecruiterProfile({
        first_name: values.first_name,
        last_name: values.last_name,
        designation: values.designation,
        phone: values.recruiter_phone,
      })
      let updatedCompany = updatedProfile.company
      if (profile.is_company_owner) {
        const companyData = new FormData()
        companyFields.forEach((field) => companyData.append(field, values[field] ?? ''))
        if (values.logo?.[0]) companyData.append('logo', values.logo[0])
        updatedCompany = await companyService.updateCompany(companyData)
      }
      const combined = { ...updatedProfile, company: updatedCompany }
      setProfile(combined)
      updateCurrentUser(combined.user)
      toast.success('Recruiter and company profile updated.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <main className="profile-page d-flex align-items-center justify-content-center"><div className="spinner-border text-primary" /></main>
  if (!profile) return <main className="profile-page"><div className="container py-5"><div className="alert alert-warning">No recruiter profile is connected to this account. Ask the administrator to configure it.</div></div></main>

  return (
    <main className="profile-page">
      <nav className="dashboard-nav">
        <div className="d-flex align-items-center gap-2"><span className="brand-mark">CC</span><span className="fw-bold fs-5">CampusConnect</span></div>
        <Link className="btn btn-outline-secondary d-flex align-items-center gap-2" to="/recruiter/dashboard"><ArrowLeft size={17} /> Dashboard</Link>
      </nav>

      <div className="container py-5">
        <div className="mb-4">
          <p className="eyebrow mb-2">Recruiter workspace</p>
          <h1 className="h2 fw-bold mb-2">Company and recruiter profile</h1>
          <p className="text-secondary mb-0">Accurate company information builds trust with colleges and candidates.</p>
        </div>

        <form onSubmit={handleSubmit(saveProfile)}>
          <div className="row g-4">
            <div className="col-12 col-lg-4">
              <section className="profile-card text-center">
                {profile.company.logo ? <img alt="Company logo" className="company-logo" src={profile.company.logo} /> : <div className="company-logo company-logo-placeholder"><Building2 size={38} /></div>}
                <h2 className="h5 fw-bold mt-3 mb-1">{profile.company.name}</h2>
                <p className="text-secondary small">{profile.company.industry}</p>
                {profile.is_company_owner ? (
                  <><label className="btn btn-outline-primary w-100" htmlFor="company-logo"><Camera className="me-2" size={17} /> Choose logo</label><input accept="image/jpeg,image/png,image/webp" className="visually-hidden" id="company-logo" type="file" {...register('logo')} /><p className="small text-secondary mt-2 mb-0">JPEG, PNG, or WebP. Maximum 2 MB.</p></>
                ) : <span className="badge text-bg-light">Company member</span>}
              </section>

              <section className="profile-card mt-4">
                <h2 className="h6 fw-bold mb-2"><ShieldCheck className="me-2" size={18} />College recruitment requests</h2>
                <p className="small text-secondary">Select a college whenever your company wants to recruit its students. The placement team will review and respond.</p>
                <div className="d-flex gap-2 mb-3">
                  <select aria-label="Select college" className="form-select" onChange={(event) => setSelectedCollege(event.target.value)} required value={selectedCollege}>
                    <option value="">Select a college to recruit from</option>
                    {colleges
                      .filter((college) => !profile.company.partnerships.some((item) => item.college.id === college.id))
                      .map((college) => <option key={college.id} value={college.id}>{college.name}</option>)}
                  </select>
                  <button aria-label="Send recruitment request" className="btn btn-primary" disabled={requesting || !selectedCollege} onClick={requestCollege} title="Send recruitment request" type="button"><Plus size={17} /></button>
                </div>
                <div className="d-grid gap-3">
                  {profile.company.partnerships.length ? profile.company.partnerships.map((partnership) => <PartnershipStatus key={partnership.id} onCancel={() => cancelRequest(partnership)} partnership={partnership} />) : <div className="portfolio-empty">No recruitment requests sent yet.</div>}
                </div>
              </section>
            </div>

            <div className="col-12 col-lg-8">
              <section className="profile-card">
                <h2 className="h5 fw-bold mb-4">Your recruiter details</h2>
                <div className="row g-3">
                  <ProfileField error={errors.first_name} label="First name" name="first_name" register={register} required />
                  <ProfileField error={errors.last_name} label="Last name" name="last_name" register={register} required />
                  <ProfileField error={errors.designation} label="Designation" name="designation" register={register} required />
                  <ProfileField label="Direct phone" name="recruiter_phone" register={register} type="tel" />
                </div>
              </section>

              <fieldset disabled={!profile.is_company_owner}>
                <section className="profile-card mt-4">
                  <div className="d-flex justify-content-between gap-3 mb-4"><h2 className="h5 fw-bold mb-0">Company details</h2>{!profile.is_company_owner && <span className="badge text-bg-warning">Owner access required</span>}</div>
                  <div className="row g-3">
                    <ProfileField label="Company name" name="name" register={register} required />
                    <ProfileField label="Industry" name="industry" register={register} required />
                    <ProfileField full label="Website" name="website" register={register} required type="url" />
                    <ProfileField label="Contact email" name="contact_email" register={register} required type="email" />
                    <ProfileField label="Company phone" name="phone" register={register} type="tel" />
                    <ProfileField label="Headquarters" name="headquarters" register={register} />
                    <ProfileField label="Company size" name="company_size" register={register} placeholder="For example, 201–500 employees" />
                    <ProfileField full label="LinkedIn URL" name="linkedin_url" register={register} type="url" />
                    <div className="col-12"><label className="form-label fw-semibold" htmlFor="description">Company description</label><textarea className="form-control" id="description" maxLength="2500" rows="5" {...register('description')} /></div>
                  </div>
                </section>
              </fieldset>

              <div className="d-flex justify-content-end mt-4"><button className="btn btn-primary btn-lg d-flex align-items-center gap-2" disabled={saving} type="submit"><Save size={18} />{saving ? 'Saving…' : 'Save profile'}</button></div>
            </div>
          </div>
        </form>
      </div>
    </main>
  )
}

function PartnershipStatus({ onCancel, partnership }) {
  const colors = { PENDING: 'warning', VERIFIED: 'success', REJECTED: 'danger', SUSPENDED: 'secondary' }
  return <div className="partnership-status"><div className="d-flex justify-content-between gap-2"><strong>{partnership.college.name}</strong>{partnership.status === 'PENDING' && <button aria-label="Cancel request" className="btn btn-sm btn-light text-danger" onClick={onCancel} title="Cancel pending request" type="button"><X size={14} /></button>}</div><span className={`badge text-bg-${colors[partnership.status]}`}>{partnership.status_display}</span>{partnership.review_note && <small>{partnership.review_note}</small>}</div>
}

function ProfileField({ error, full = false, label, name, register, required = false, ...props }) {
  return <div className={full ? 'col-12' : 'col-12 col-md-6'}><label className="form-label fw-semibold" htmlFor={name}>{label}</label><input className={`form-control ${error ? 'is-invalid' : ''}`} id={name} {...props} {...register(name, required ? { required: `${label} is required.` } : {})} />{error && <div className="invalid-feedback">{error.message}</div>}</div>
}

export default RecruiterCompanyPage
