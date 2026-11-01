import { yupResolver } from '@hookform/resolvers/yup'
import { KeyRound } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { useNavigate, useParams } from 'react-router-dom'
import * as yup from 'yup'

import PasswordField from '../../components/PasswordField.jsx'
import { authService } from '../../services/authService.js'
import { getApiErrorMessage } from '../../utils/apiErrors.js'

const schema = yup.object({
  password: yup.string().min(8, 'Use at least 8 characters.').required('Password is required.'),
  password_confirm: yup.string().oneOf([yup.ref('password')], 'Passwords must match.').required('Confirm your password.'),
})

function ResetPasswordPage({ activation = false }) {
  const [submitting, setSubmitting] = useState(false)
  const { uid, token } = useParams()
  const navigate = useNavigate()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({ resolver: yupResolver(schema) })

  const onSubmit = async (values) => {
    setSubmitting(true)
    try {
      await authService.confirmPasswordReset({ uid, token, ...values })
      toast.success(activation ? 'Account activated. You can now sign in.' : 'Password reset successfully. Sign in through your portal.')
      navigate(activation ? '/student/login' : '/', { replace: true })
    } catch (error) {
      toast.error(getApiErrorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <span className="portal-icon mb-3"><KeyRound aria-hidden="true" size={23} /></span>
        <p className="eyebrow mb-2">{activation ? 'Student account invitation' : 'Account recovery'}</p>
        <h1 className="h2 fw-bold mb-3">{activation ? 'Activate your account' : 'Choose a new password'}</h1>
        <p className="text-secondary mb-4">{activation ? 'Choose a private password to finish setting up the account created by your college.' : 'Use a strong password you do not use on another service.'}</p>
        <form noValidate onSubmit={handleSubmit(onSubmit)}>
          <PasswordField autoComplete="new-password" error={errors.password} id="new-password" label="New password" name="password" register={register} />
          <PasswordField autoComplete="new-password" error={errors.password_confirm} id="confirm-password" label="Confirm new password" name="password_confirm" register={register} />

          <button className="btn btn-primary btn-lg w-100 mt-4" disabled={submitting} type="submit">
            {submitting ? 'Saving…' : activation ? 'Activate account' : 'Reset password'}
          </button>
        </form>
      </section>
    </main>
  )
}

export default ResetPasswordPage
