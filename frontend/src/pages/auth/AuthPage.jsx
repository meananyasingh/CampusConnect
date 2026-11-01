import { yupResolver } from '@hookform/resolvers/yup'
import { ArrowLeft, BriefcaseBusiness, GraduationCap, ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import * as yup from 'yup'

import PasswordField from '../../components/PasswordField.jsx'
import { useAuth } from '../../hooks/useAuth.js'
import { authService } from '../../services/authService.js'
import { collegeService } from '../../services/collegeService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const portalDetails = {
  STUDENT: {
    title: 'Student',
    icon: GraduationCap,
    loginPath: '/student/login',
    signupPath: '/student/signup',
    dashboardPath: '/student/dashboard',
  },
  RECRUITER: {
    title: 'Recruiter',
    icon: BriefcaseBusiness,
    loginPath: '/recruiter/login',
    signupPath: '/recruiter/signup',
    dashboardPath: '/recruiter/dashboard',
  },
  ADMIN: {
    title: 'College Admin',
    icon: ShieldCheck,
    loginPath: '/admin-login',
    dashboardPath: '/admin-dashboard',
  },
}

const loginSchema = yup.object({
  email: yup.string().email('Enter a valid email address.').required('Email is required.'),
  password: yup.string().required('Password is required.'),
})

const signupSchema = loginSchema.shape({
  first_name: yup.string().trim().required('First name is required.'),
  last_name: yup.string().trim().required('Last name is required.'),
  password: yup.string().min(8, 'Use at least 8 characters.').required('Password is required.'),
  password_confirm: yup
    .string()
    .oneOf([yup.ref('password')], 'Passwords must match.')
    .required('Confirm your password.'),
})

const studentSignupSchema = signupSchema.shape({
  college: yup.string().required('College is required.'),
  program: yup.string().required('Degree and branch are required.'),
  enrollment_number: yup.string().trim().min(3, 'Use at least 3 characters.').required('Enrollment number is required.'),
  graduation_year: yup.string().matches(/^\d{4}$/, 'Enter a four-digit year.').required('Graduation year is required.'),
})

const websiteSchema = yup
  .string()
  .transform((value) => {
    const trimmed = value?.trim()
    if (trimmed && !/^https?:\/\//i.test(trimmed)) return `https://${trimmed}`
    return trimmed
  })
  .url('Enter a valid company website.')
  .required('Company website is required.')

const recruiterSignupSchema = signupSchema.shape({
  company_name: yup.string().trim().required('Company name is required.'),
  company_industry: yup.string().trim().required('Industry is required.'),
  company_website: websiteSchema,
  company_email: yup.string().email('Enter a valid company email.').required('Company email is required.'),
  designation: yup.string().trim().required('Designation is required.'),
  phone: yup.string().trim(),
})

function FormField({ error, label, name, register, type = 'text' }) {
  if (type === 'password') {
    return <PasswordField error={error} label={label} name={name} register={register} />
  }
  return (
    <div className="mb-3 text-start">
      <label className="form-label fw-semibold" htmlFor={name}>{label}</label>
      <input
        className={`form-control form-control-lg ${error ? 'is-invalid' : ''}`}
        id={name}
        type={type}
        {...register(name)}
      />
      {error && <div className="invalid-feedback">{error.message}</div>}
    </div>
  )
}

function AuthPage({ mode, role }) {
  const [submitting, setSubmitting] = useState(false)
  const [colleges, setColleges] = useState([])
  const [programs, setPrograms] = useState([])
  const [loadingColleges, setLoadingColleges] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const portal = portalDetails[role]
  const Icon = portal.icon
  const isSignup = mode === 'signup'
  const isStudentSignup = isSignup && role === 'STUDENT'
  const isRecruiterSignup = isSignup && role === 'RECRUITER'
  const {
    register,
    handleSubmit,
    control,
    setValue,
    formState: { errors },
  } = useForm({
    resolver: yupResolver(
      isStudentSignup
        ? studentSignupSchema
        : isRecruiterSignup
          ? recruiterSignupSchema
          : isSignup ? signupSchema : loginSchema,
    ),
  })
  const selectedCollege = useWatch({ control, name: 'college' })
  const collegeField = register('college')

  useEffect(() => {
    if (!isStudentSignup) return

    const loadColleges = async () => {
      setLoadingColleges(true)
      try {
        setColleges(await collegeService.list())
      } catch (error) {
        toast.error(getApiErrorMessage(error))
      } finally {
        setLoadingColleges(false)
      }
    }

    loadColleges()
  }, [isStudentSignup])

  useEffect(() => {
    if (!isStudentSignup || !selectedCollege) return

    const loadPrograms = async () => {
      try {
        setPrograms(await collegeService.listPrograms(selectedCollege))
      } catch (error) {
        toast.error(getApiErrorMessage(error))
      }
    }

    loadPrograms()
  }, [isStudentSignup, selectedCollege, setValue])

  const onSubmit = async (values) => {
    setSubmitting(true)
    try {
      if (isSignup) {
        await authService.register(role, values)
        toast.success('Account created. You can now sign in.')
        navigate(portal.loginPath, { replace: true })
      } else {
        await login(role, values)
        toast.success(`Welcome to the ${portal.title} portal.`)
        navigate(location.state?.from?.pathname || portal.dashboardPath, { replace: true })
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <Link className="portal-link mb-4" to="/">
          <ArrowLeft aria-hidden="true" size={17} /> Home
        </Link>
        <span className="portal-icon mb-3"><Icon aria-hidden="true" size={23} /></span>
        <p className="eyebrow mb-2">{portal.title} portal</p>
        <h1 className="h2 fw-bold mb-2">{isSignup ? 'Create your account' : 'Welcome back'}</h1>
        <p className="text-secondary mb-4">
          {isSignup ? 'Start your CampusConnect journey.' : 'Sign in with your registered email.'}
        </p>

        <form noValidate onSubmit={handleSubmit(onSubmit)}>
          {isSignup && (
            <div className="row g-2">
              <div className="col-sm-6">
                <FormField error={errors.first_name} label="First name" name="first_name" register={register} />
              </div>
              <div className="col-sm-6">
                <FormField error={errors.last_name} label="Last name" name="last_name" register={register} />
              </div>
            </div>
          )}
          {isStudentSignup && (
            <>
              <div className="mb-3 text-start">
                <label className="form-label fw-semibold" htmlFor="college">College</label>
                <select
                  className={`form-select form-select-lg ${errors.college ? 'is-invalid' : ''}`}
                  disabled={loadingColleges}
                  id="college"
                  {...collegeField}
                  onChange={(event) => {
                    collegeField.onChange(event)
                    setValue('program', '')
                    setPrograms([])
                  }}
                >
                  <option value="">{loadingColleges ? 'Loading colleges…' : 'Select your college'}</option>
                  {colleges.map((college) => (
                    <option key={college.id} value={college.id}>{college.name}</option>
                  ))}
                </select>
                {errors.college && <div className="invalid-feedback">{errors.college.message}</div>}
              </div>
              <div className="mb-3 text-start">
                <label className="form-label fw-semibold" htmlFor="program">Degree and branch</label>
                <select
                  className={`form-select form-select-lg ${errors.program ? 'is-invalid' : ''}`}
                  disabled={!selectedCollege}
                  id="program"
                  {...register('program')}
                >
                  <option value="">Select your program</option>
                  {programs.map((program) => (
                    <option key={program.id} value={program.id}>
                      {program.degree_display} — {program.branch}
                    </option>
                  ))}
                </select>
                {errors.program && <div className="invalid-feedback">{errors.program.message}</div>}
              </div>
              <div className="row g-2">
                <div className="col-sm-7">
                  <FormField error={errors.enrollment_number} label="Enrollment number" name="enrollment_number" register={register} />
                </div>
                <div className="col-sm-5">
                  <FormField error={errors.graduation_year} label="Graduation year" name="graduation_year" register={register} type="number" />
                </div>
              </div>
              {!loadingColleges && colleges.length === 0 && (
                <div className="alert alert-warning small" role="status">
                  No active college is configured yet. A system administrator must add one before student registration.
                </div>
              )}
            </>
          )}
          {isRecruiterSignup && (
            <>
              <FormField error={errors.company_name} label="Company name" name="company_name" register={register} />
              <div className="row g-2">
                <div className="col-sm-6"><FormField error={errors.company_industry} label="Industry" name="company_industry" register={register} /></div>
                <div className="col-sm-6"><FormField error={errors.designation} label="Your designation" name="designation" register={register} /></div>
              </div>
              <FormField error={errors.company_website} label="Company website" name="company_website" register={register} type="url" />
              <FormField error={errors.company_email} label="Company contact email" name="company_email" register={register} type="email" />
              <FormField error={errors.phone} label="Your phone (optional)" name="phone" register={register} type="tel" />
            </>
          )}
          <FormField error={errors.email} label="Email address" name="email" register={register} type="email" />
          <PasswordField autoComplete={isSignup ? 'new-password' : 'current-password'} error={errors.password} label="Password" name="password" register={register} />
          {!isSignup && (
            <div className="text-end mt-n2 mb-3">
              <Link className="small fw-semibold" to="/forgot-password">Forgot password?</Link>
            </div>
          )}
          {isSignup && (
            <PasswordField
              autoComplete="new-password"
              error={errors.password_confirm}
              label="Confirm password"
              name="password_confirm"
              register={register}
            />
          )}
          <button className="btn btn-primary btn-lg w-100 mt-2" disabled={submitting} type="submit">
            {submitting ? 'Please wait…' : isSignup ? 'Create account' : 'Sign in'}
          </button>
        </form>

        {role !== 'ADMIN' && (
          <p className="text-center text-secondary mt-4 mb-0">
            {isSignup ? 'Already registered?' : 'New to CampusConnect?'}{' '}
            <Link to={isSignup ? portal.loginPath : portal.signupPath}>
              {isSignup ? 'Sign in' : 'Create an account'}
            </Link>
          </p>
        )}
        {role === 'ADMIN' && (
          <p className="small text-secondary text-center mt-4 mb-0">
            Administrator accounts are created securely and cannot be registered publicly.
          </p>
        )}
      </section>
    </main>
  )
}

export default AuthPage
