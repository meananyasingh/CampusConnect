import { useCallback, useEffect, useRef, useState } from 'react'
import { AlertTriangle, X } from 'lucide-react'

import { ConfirmDialogContext } from './confirm-dialog-context.js'

export function ConfirmDialogProvider({ children }) {
  const [dialog, setDialog] = useState(null)
  const cancelButtonRef = useRef(null)

  const confirm = useCallback((options) => new Promise((resolve) => {
    setDialog({
      confirmLabel: 'Confirm',
      title: 'Please confirm',
      tone: 'danger',
      ...options,
      resolve,
    })
  }), [])

  const close = useCallback((answer) => {
    setDialog((current) => {
      current?.resolve(answer)
      return null
    })
  }, [])

  useEffect(() => {
    if (!dialog) return undefined
    cancelButtonRef.current?.focus()
    const onKeyDown = (event) => {
      if (event.key === 'Escape') close(false)
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [close, dialog])

  return (
    <ConfirmDialogContext.Provider value={confirm}>
      {children}
      {dialog && (
        <div className="confirm-dialog-backdrop" onMouseDown={() => close(false)}>
          <section
            aria-describedby="confirm-dialog-message"
            aria-labelledby="confirm-dialog-title"
            aria-modal="true"
            className="confirm-dialog"
            onMouseDown={(event) => event.stopPropagation()}
            role="alertdialog"
          >
            <button aria-label="Close confirmation" className="confirm-dialog-close" onClick={() => close(false)} type="button"><X size={19} /></button>
            <span className={`confirm-dialog-icon ${dialog.tone}`}><AlertTriangle size={24} /></span>
            <h2 id="confirm-dialog-title">{dialog.title}</h2>
            <p id="confirm-dialog-message">{dialog.message}</p>
            <div className="confirm-dialog-actions">
              <button className="btn btn-light" onClick={() => close(false)} ref={cancelButtonRef} type="button">Cancel</button>
              <button className={`btn ${dialog.tone === 'danger' ? 'btn-danger' : 'btn-primary'}`} onClick={() => close(true)} type="button">{dialog.confirmLabel}</button>
            </div>
          </section>
        </div>
      )}
    </ConfirmDialogContext.Provider>
  )
}
