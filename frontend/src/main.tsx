import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './index.css'
import App from './app/App.tsx'
import { AppProviders } from './app/providers.tsx'

const router = createBrowserRouter([{ path: '*', element: <AppProviders><App /></AppProviders> }])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
