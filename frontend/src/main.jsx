import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import 'bootstrap/dist/css/bootstrap.min.css'
import { Toaster } from 'react-hot-toast'
import './index.css'
import App from './App.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import { ConfirmDialogProvider } from './context/ConfirmDialogContext.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <ConfirmDialogProvider>
          <App />
          <Toaster position="top-right" toastOptions={{ duration: 4000 }} />
        </ConfirmDialogProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
