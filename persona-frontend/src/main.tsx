import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import PersonaApp from './PersonaApp.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <PersonaApp />
  </StrictMode>,
)
