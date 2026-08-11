import { useEffect, useRef } from 'react'
import { NavLink } from 'react-router-dom'

import { useAuth } from '../features/auth/useAuth'
import { Icon } from './Icon'
import { getVisibleNavItems, type ShellNavGroup, type ShellNavItem } from './navigation'

type SidebarProps = {
  isOpen: boolean
  onClose: () => void
  onLogout: () => void
}

export function Sidebar({ isOpen, onClose, onLogout }: SidebarProps) {
  const sidebarRef = useRef<HTMLElement>(null)
  const restoreFocusRef = useRef<HTMLElement | null>(null)
  const { user } = useAuth()
  const visibleItems = getVisibleNavItems(user)
  const managementLinks = visibleItems.filter((item) => item.group === 'Gestion')
  const operationLinks = visibleItems.filter((item) => item.group === 'Operativo')
  const accountLinks = visibleItems.filter((item) => item.group === 'Cuenta')

  useEffect(() => {
    if (!isOpen) return undefined
    restoreFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null
    const focusable = () => Array.from(sidebarRef.current?.querySelectorAll<HTMLElement>('a[href],button:not([disabled])') ?? [])
    focusable()[0]?.focus()
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { onClose(); return }
      if (event.key !== 'Tab') return
      const items = focusable(); if (!items.length) return
      const first = items[0]; const last = items.at(-1)!
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => { window.removeEventListener('keydown', onKeyDown); restoreFocusRef.current?.focus(); restoreFocusRef.current = null }
  }, [isOpen, onClose])

  return (
    <>
      <button className={`shell-backdrop ${isOpen ? 'shell-backdrop--visible' : ''}`} type="button" aria-label="Cerrar menu" onClick={onClose} />
      <aside ref={sidebarRef} id="shell-sidebar" className={`shell-sidebar ${isOpen ? 'nav-active' : ''}`} aria-label="Navegacion principal">
        <div className="shell-sidebar__inner">
          <NavGroup caption="Gestion" links={managementLinks} onNavigate={onClose} />
          {operationLinks.length > 0 && <NavGroup caption="Operativo" links={operationLinks} onNavigate={onClose} />}
          <div className="shell-nav-card">
            <p className="shell-nav-caption">Cuenta</p>
            {accountLinks.map((link) => <NavItem key={link.id} link={link} onNavigate={onClose} />)}
            <button className="shell-nav-link" type="button" onClick={onLogout}><Icon name="logout" /><span>Salir</span></button>
          </div>
        </div>
      </aside>
    </>
  )
}

function NavGroup({ caption, links, onNavigate }: { caption: ShellNavGroup, links: ShellNavItem[], onNavigate: () => void }) {
  return (
    <div className="shell-nav-card">
      <p className="shell-nav-caption">{caption}</p>
      <ul>
        {links.map((link) => (
          <li key={link.label}>
            <NavItem link={link} onNavigate={onNavigate} />
          </li>
        ))}
      </ul>
    </div>
  )
}

function NavItem({ link, onNavigate }: { link: ShellNavItem, onNavigate?: () => void }) {
  return (
    <NavLink
      className={({ isActive }) => `shell-nav-link ${isActive ? 'shell-nav-link--active' : ''}`}
      end={link.to === '/app'}
      to={link.to}
      onClick={onNavigate}
    >
      <Icon name={link.icon} />
      <span>{link.label}</span>
    </NavLink>
  )
}
