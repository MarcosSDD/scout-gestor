import { canSeeVisualAccess, hasPersona, hasUnidadRole, isAdminUser, isApoderado, isGrupoResponsable, isSuperuser } from './rbac'
import type { AuthUser } from './authTypes'

function user(overrides: Partial<AuthUser> = {}): AuthUser {
  return {
    id: 1,
    username: 'usuario',
    email: 'usuario@scouts.cl',
    first_name: 'Ana',
    last_name: 'Rojas',
    is_staff: false,
    is_superuser: false,
    persona_id: null,
    responsable_grupo_ids: [],
    unidad_roles: [],
    is_apoderado: false,
    ...overrides,
  }
}

describe('visual RBAC helpers', () => {
  it('treats staff and superusers as admin users', () => {
    expect(isAdminUser(user({ is_staff: true }))).toBe(true)
    expect(isAdminUser(user({ is_superuser: true }))).toBe(true)
    expect(isAdminUser(user())).toBe(false)
  })

  it('requires is_superuser for the superuser visual permission', () => {
    expect(isSuperuser(user({ is_staff: true }))).toBe(false)
    expect(canSeeVisualAccess(user({ is_staff: true }), 'superuser')).toBe(false)
    expect(canSeeVisualAccess(user({ is_superuser: true }), 'superuser')).toBe(true)
  })

  it('detects scoped user roles from /auth/me fields', () => {
    expect(isGrupoResponsable(user({ responsable_grupo_ids: [12] }))).toBe(true)
    expect(hasUnidadRole(user({ unidad_roles: [{ unidad_id: 3, rol: 'RESPONSABLE' }] }))).toBe(true)
    expect(isApoderado(user({ is_apoderado: true }))).toBe(true)
    expect(hasPersona(user({ persona_id: 7 }))).toBe(true)
  })

  it('grants visual access by role without requiring duplicate logic in components', () => {
    expect(canSeeVisualAccess(user({ is_superuser: true }), 'admin')).toBe(true)
    expect(canSeeVisualAccess(user({ responsable_grupo_ids: [1] }), 'grupo')).toBe(true)
    expect(canSeeVisualAccess(user({ responsable_grupo_ids: [1] }), 'unidad')).toBe(true)
    expect(canSeeVisualAccess(user({ unidad_roles: [{ unidad_id: 1, rol: 'ASISTENTE' }] }), ['grupo', 'unidad'])).toBe(true)
    expect(canSeeVisualAccess(user({ is_apoderado: true }), 'grupo')).toBe(false)
    expect(canSeeVisualAccess(null, 'authenticated')).toBe(false)
  })
})
