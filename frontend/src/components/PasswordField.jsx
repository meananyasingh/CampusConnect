import { Eye, EyeOff } from 'lucide-react'
import { useState } from 'react'

function PasswordField({ autoComplete, error, id, label, name, register }) {
  const [isVisible, setIsVisible] = useState(false)
  const inputId = id || name
  const errorId = `${inputId}-error`

  return (
    <div className="mb-3 text-start">
      <label className="form-label fw-semibold" htmlFor={inputId}>{label}</label>
      <div className="password-control">
        <input
          aria-describedby={error ? errorId : undefined}
          aria-invalid={Boolean(error)}
          autoComplete={autoComplete}
          className={`form-control form-control-lg ${error ? 'is-invalid' : ''}`}
          id={inputId}
          type={isVisible ? 'text' : 'password'}
          {...register(name)}
        />
        <button
          aria-label={isVisible ? 'Hide password' : 'Show password'}
          aria-pressed={isVisible}
          className="password-toggle"
          onClick={() => setIsVisible((current) => !current)}
          type="button"
        >
          {isVisible ? <EyeOff aria-hidden="true" size={20} /> : <Eye aria-hidden="true" size={20} />}
        </button>
      </div>
      {error && <div className="invalid-feedback d-block" id={errorId}>{error.message}</div>}
    </div>
  )
}

export default PasswordField
