import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import SetupWizard from './SetupWizard'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <SetupWizard />
  </StrictMode>,
)
