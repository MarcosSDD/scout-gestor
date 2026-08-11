import { useEffect, useRef, useState, type PropsWithChildren } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'

import { useAuth } from '../features/auth/useAuth'
import { AppHeader } from './AppHeader'
import { MobileBottomNav } from './MobileBottomNav'
import { Sidebar } from './Sidebar'

export function AppShell({ children }: PropsWithChildren) {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuth()
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const mainRef = useRef<HTMLElement>(null)

  useEffect(() => {
    mainRef.current?.focus()
  }, [location.pathname])

  async function handleLogout() {
    await logout()
    toast.success('Sesion cerrada')
    navigate('/login')
  }

  return (
    <div className="shell-wrapper">
      <a className="skip-link" href="#main-content">Saltar al contenido principal</a>
      <AppHeader
        user={user}
        onMenuClick={() => setIsSidebarOpen((current) => !current)}
        isMenuOpen={isSidebarOpen}
      />
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} onLogout={handleLogout} />
      <main ref={mainRef} id="main-content" className="shell-main" tabIndex={-1}>
        <div className="shell-main__bottom">
          <div className="shell-main__left">{children}</div>
        </div>
      </main>
      <MobileBottomNav />
    </div>
  )
}
