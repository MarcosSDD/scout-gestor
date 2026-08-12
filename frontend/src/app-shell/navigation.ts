import type { AuthUser } from '../features/auth/authTypes'
import { canSeeVisualAccess, type VisualAccessRule } from '../features/auth/rbac'
import type { IconName } from './Icon'

export type ShellNavGroup = 'Gestion' | 'Operativo' | 'Cuenta'

export type ShellNavItemId = 'dashboard' | 'grupos' | 'personas' | 'unidades' | 'formacion' | 'perfil'

export type ShellNavItem = {
  id: ShellNavItemId
  label: string
  icon: IconName
  to: string
  group: ShellNavGroup
  visibleWhen: VisualAccessRule
  showInHeader?: boolean
  showInMobile?: boolean
  showInRightPanel?: boolean
}

export const shellNavItems: ShellNavItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: 'home',
    to: '/app',
    group: 'Gestion',
    visibleWhen: 'authenticated',
    showInHeader: true,
    showInMobile: true,
  },
  {
    id: 'grupos',
    label: 'Grupos',
    icon: 'users',
    to: '/app/grupos',
    group: 'Gestion',
    visibleWhen: 'superuser',
    showInHeader: true,
    showInMobile: true,
    showInRightPanel: true,
  },
  {
    id: 'personas',
    label: 'Personas',
    icon: 'user',
    to: '/app/personas',
    group: 'Gestion',
    visibleWhen: ['admin', 'grupo', 'unidad'],
    showInMobile: true,
  },
  {
    id: 'unidades',
    label: 'Unidades',
    icon: 'layers',
    to: '/app/unidades',
    group: 'Gestion',
    visibleWhen: ['admin', 'grupo', 'unidad'],
    showInHeader: true,
    showInMobile: true,
    showInRightPanel: true,
  },
  {
    id: 'formacion',
    label: 'Formacion',
    icon: 'shield',
    to: '/app/formacion',
    group: 'Operativo',
    visibleWhen: ['admin', 'grupo', 'unidad'],
  },
  {
    id: 'perfil',
    label: 'Mi perfil',
    icon: 'settings',
    to: '/app/perfil',
    group: 'Cuenta',
    visibleWhen: 'persona',
    showInMobile: true,
    showInRightPanel: true,
  },
]

export function getVisibleNavItems(user: AuthUser | null) {
  return shellNavItems.filter((item) => canSeeNavItem(user, item))
}

export function canSeeNavItem(user: AuthUser | null, item: ShellNavItem) {
  return canSeeVisualAccess(user, item.visibleWhen)
}

export function getNavItemById(id: ShellNavItemId) {
  return shellNavItems.find((item) => item.id === id)
}
