import type { AuthUser } from './authTypes'

export type VisualPermission = 'authenticated' | 'admin' | 'grupo' | 'unidad' | 'apoderado' | 'persona'

export type VisualAccessRule = VisualPermission | VisualPermission[]

export function isAdminUser(user: AuthUser | null) {
  return !!user && (user.is_staff || user.is_superuser)
}

export function isGrupoResponsable(user: AuthUser | null) {
  return !!user && user.responsable_grupo_ids.length > 0
}

export function hasUnidadRole(user: AuthUser | null) {
  return !!user && user.unidad_roles.length > 0
}

export function isApoderado(user: AuthUser | null) {
  return !!user && user.is_apoderado
}

export function hasPersona(user: AuthUser | null) {
  return !!user && user.persona_id !== null
}

export function hasVisualPermission(user: AuthUser | null, permission: VisualPermission) {
  if (!user) {
    return false
  }

  if (permission === 'authenticated') {
    return true
  }

  if (isAdminUser(user)) {
    return true
  }

  if (permission === 'admin') {
    return false
  }

  if (permission === 'grupo') {
    return isGrupoResponsable(user)
  }

  if (permission === 'unidad') {
    return hasUnidadRole(user) || isGrupoResponsable(user)
  }

  if (permission === 'apoderado') {
    return isApoderado(user)
  }

  return hasPersona(user)
}

export function canSeeVisualAccess(user: AuthUser | null, rule: VisualAccessRule) {
  const permissions = Array.isArray(rule) ? rule : [rule]
  return permissions.some((permission) => hasVisualPermission(user, permission))
}
