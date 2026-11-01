import { ArrowLeft, Camera, Save } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'

import { useAuth } from '../../hooks/useAuth.js'
import { studentService } from '../../services/studentService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const editableFields = [
  'first_name',
  'last_name',
  'phone',
  'date_of_birth',
  'location',
  'career_objective',
  'linkedin_url',
  'github_url',
  'portfolio_url',
  'preferred_job_role',
  'preferred_locations',
  'is_visible_to_recruiters',
  'cgpa',
  'tenth_percentage',
  'twelfth_percentage',
  'active_backlogs',
]

function StudentProfilePage() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const { updateCurrentUser } = useAuth()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm()

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const data = await studentService.getProfile()
        setProfile(data)
        reset({
          first_name: data.user.first_name,
          last_name: data.user.last_name,
          phone: data.phone || '',
          date_of_birth: data.date_of_birth || '',
          location: data.location || '',
          career_objective: data.career_objective || '',
          linkedin_url: data.linkedin_url || '',
          github_url: data.github_url || '',
          portfolio_url: data.portfolio_url || '',
          preferred_job_role: data.preferred_job_role || '',
          preferred_locations: data.preferred_locations || '',
          is_visible_to_recruiters: data.is_visible_to_recruiters,
          cgpa: data.cgpa || '',
          tenth_percentage: data.tenth_percentage || '',
          twelfth_percentage: data.twelfth_percentage || '',
          active_backlogs: data.active_backlogs ?? 0,
        })
      } catch (error) {
        toast.error(getApiErrorMessage(error))
      } finally {
        setLoading(false)
      }
    }

    loadProfile()
  }, [reset])

  const onSubmit = async (values) => {
    setSaving(true)
    const formData = new FormData()
    editableFields.forEach((field) => formData.append(field, values[field] ?? ''))
    if (values.profile_picture?.[0]) {
      formData.append('profile_picture', values.profile_picture[0])
    }

    try {
      const updatedProfile = await studentService.updateProfile(formData)
      setProfile(updatedProfile)
      updateCurrentUser(updatedProfile.user)
      toast.success('Profile updated successfully.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <main className="profile-page d-flex align-items-center justify-content-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading profile…</span>
        </div>
      </main>
    )
  }

  if (!profile) {
    return <main className="profile-page"><div className="container py-5"><div className="alert alert-danger">Your student profile could not be loaded.</div></div></main>
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
        <div className="mb-4">
          <p className="eyebrow mb-2">Student workspace</p>
          <h1 className="h2 fw-bold mb-2">Personal and academic profile</h1>
          <p className="text-secondary mb-0">Keep your details accurate so eligibility checks work correctly.</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="row g-4">
            <div className="col-12 col-lg-4">
              <section className="profile-card text-center">
                {profile.profile_picture ? (
                  <img className="profile-avatar" src={profile.profile_picture} alt="Student profile" />
                ) : (
                  <div className="profile-avatar profile-avatar-placeholder">
                    {profile.user.first_name?.[0] || profile.user.email[0]}
                  </div>
                )}
                <h2 className="h5 fw-bold mt-3 mb-1">{profile.user.first_name} {profile.user.last_name}</h2>
                <p className="text-secondary small">{profile.user.email}</p>
                <label className="btn btn-outline-primary w-100 mt-2" htmlFor="profile-picture">
                  <Camera aria-hidden="true" className="me-2" size={17} /> Choose picture
                </label>
                <input
                  accept="image/jpeg,image/png,image/webp"
                  className="visually-hidden"
                  id="profile-picture"
                  type="file"
                  {...register('profile_picture')}
                />
                <p className="small text-secondary mt-2 mb-0">JPEG, PNG, or WebP. Maximum 2 MB.</p>
              </section>

              <section className="profile-card mt-4">
                <h2 className="h6 fw-bold mb-3">College identity</h2>
                <dl className="profile-details mb-0">
                  <dt>College</dt><dd>{profile.college.name}</dd>
                  <dt>Program</dt><dd>{profile.program.degree_display}</dd>
                  <dt>Branch</dt><dd>{profile.program.branch}</dd>
                  <dt>Enrollment</dt><dd>{profile.enrollment_number}</dd>
                  <dt>Graduation</dt><dd>{profile.graduation_year}</dd>
                </dl>
              </section>

              <section className="profile-card mt-4">
                <h2 className="h5 fw-bold mb-4">Career presence and preferences</h2>
                <div className="row g-3">
                  <ProfileInput full label="LinkedIn URL" name="linkedin_url" register={register} type="url" />
                  <ProfileInput full label="GitHub URL" name="github_url" register={register} type="url" />
                  <ProfileInput full label="Portfolio URL" name="portfolio_url" register={register} type="url" />
                  <ProfileInput label="Preferred job role" name="preferred_job_role" register={register} />
                  <ProfileInput label="Preferred locations" name="preferred_locations" register={register} />
                  <div className="col-12"><div className="form-check form-switch recruiter-visibility-switch"><input className="form-check-input" id="recruiter-visibility" type="checkbox" {...register('is_visible_to_recruiters')} /><label className="form-check-label fw-semibold" htmlFor="recruiter-visibility">Visible to verified recruiters</label><p className="small text-secondary mb-0">Only recruiters approved by your college can discover your professional profile and primary resume.</p></div></div>
                </div>
              </section>
            </div>

            <div className="col-12 col-lg-8">
              <section className="profile-card">
                <h2 className="h5 fw-bold mb-4">Personal details</h2>
                <div className="row g-3">
                  <ProfileInput error={errors.first_name} label="First name" name="first_name" register={register} required />
                  <ProfileInput error={errors.last_name} label="Last name" name="last_name" register={register} required />
                  <ProfileInput label="Phone" name="phone" register={register} type="tel" />
                  <ProfileInput label="Date of birth" name="date_of_birth" register={register} type="date" />
                  <ProfileInput full label="Location" name="location" register={register} />
                  <div className="col-12">
                    <label className="form-label fw-semibold" htmlFor="career_objective">Career objective</label>
                    <textarea className="form-control" id="career_objective" maxLength="1000" rows="4" {...register('career_objective')} />
                  </div>
                </div>
              </section>

              <section className="profile-card mt-4">
                <h2 className="h5 fw-bold mb-4">Academic performance</h2>
                <div className="row g-3">
                  <ProfileInput label="Current CGPA" max="10" min="0" name="cgpa" register={register} step="0.01" type="number" />
                  <ProfileInput label="10th percentage" max="100" min="0" name="tenth_percentage" register={register} step="0.01" type="number" />
                  <ProfileInput label="12th percentage" max="100" min="0" name="twelfth_percentage" register={register} step="0.01" type="number" />
                  <ProfileInput label="Active backlogs" min="0" name="active_backlogs" register={register} step="1" type="number" />
                </div>
              </section>

              <div className="d-flex justify-content-end mt-4">
                <button className="btn btn-primary btn-lg d-flex align-items-center gap-2" disabled={saving} type="submit">
                  <Save aria-hidden="true" size={18} /> {saving ? 'Saving…' : 'Save profile'}
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </main>
  )
}

function ProfileInput({ error, full = false, label, name, register, required = false, ...inputProps }) {
  return (
    <div className={full ? 'col-12' : 'col-12 col-md-6'}>
      <label className="form-label fw-semibold" htmlFor={name}>{label}</label>
      <input
        className={`form-control ${error ? 'is-invalid' : ''}`}
        id={name}
        {...inputProps}
        {...register(name, required ? { required: `${label} is required.` } : {})}
      />
      {error && <div className="invalid-feedback">{error.message}</div>}
    </div>
  )
}

export default StudentProfilePage
