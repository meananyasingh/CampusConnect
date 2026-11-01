import { yupResolver } from '@hookform/resolvers/yup'
import { ArrowLeft, Mail } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'
import * as yup from 'yup'

import { authService } from '../../services/authService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const schema = yup.object({
  email: yup.string().email('Enter a valid email address.').required('Email is required.'),
})

function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({ resolver: yupResolver(schema) })

  const onSubmit = async ({ email }) => {
    setSubmitting(true)
    try {
      await authService.requestPasswordReset(email)
      setSubmitted(true)
      toast.success('Password reset request received.')
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <Link className="portal-link mb-4" to="/"><ArrowLeft aria-hidden="true" size={17} /> Home</Link>
        <span className="portal-icon mb-3"><Mail aria-hidden="true" size={23} /></span>
        <p className="eyebrow mb-2">Account recovery</p>
        <h1 className="h2 fw-bold mb-3">Forgot your password?</h1>
        {submitted ? (
          <div className="alert alert-success mb-0" role="status">
            If an active account exists for that email, reset instructions have been sent.
          </div>
        ) : (
          <>
            <p className="text-secondary mb-4">Enter your registered email and we will send a one-time reset link.</p>
            <form noValidate onSubmit={handleSubmit(onSubmit)}>
              <label className="form-label fw-semibold" htmlFor="reset-email">Email address</label>
              <input
                className={`form-control form-control-lg ${errors.email ? 'is-invalid' : ''}`}
                id="reset-email"
                type="email"
                {...register('email')}
              />
              {errors.email && <div className="invalid-feedback">{errors.email.message}</div>}
              <button className="btn btn-primary btn-lg w-100 mt-4" disabled={submitting} type="submit">
                {submitting ? 'Sending…' : 'Send reset link'}
              </button>
            </form>
          </>
        )}
      </section>
    </main>
  )
}

export default ForgotPasswordPage
