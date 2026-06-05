import type { ApiSuccess } from '../../api/types'

export type AuthUser = {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  is_staff: boolean
  is_superuser: boolean
  persona_id: number | null
  responsable_grupo_ids: number[]
  unidad_roles: Array<{
    unidad_id: number
    rol: string
  }>
  is_apoderado: boolean
}

export type LoginCredentials = {
  username: string
  password: string
}

export type LoginData = {
  access: string
  refresh: string
  user: AuthUser
}

export type LoginResponse = ApiSuccess<LoginData>

export type RefreshTokenData = {
  access: string
  refresh: string
}

export type RefreshTokenResponse = ApiSuccess<RefreshTokenData>

export type MeResponse = ApiSuccess<AuthUser>

export type LogoutResponse = ApiSuccess<null>
