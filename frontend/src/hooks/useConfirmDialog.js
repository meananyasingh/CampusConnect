import { useContext } from 'react'

import { ConfirmDialogContext } from '../context/confirm-dialog-context.js'

export function useConfirmDialog() {
  const context = useContext(ConfirmDialogContext)
  if (!context) throw new Error('useConfirmDialog must be used inside ConfirmDialogProvider.')
  return context
}
