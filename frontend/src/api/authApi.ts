import { httpClient } from './httpClient'
import type { LoginCredentials, LoginResponse, LogoutResponse, MeResponse, RefreshTokenResponse } from '../features/auth/authTypes'

export async function login(credentials: LoginCredentials): Promise<LoginResponse> {
  const { data } = await httpClient.post<LoginResponse>('/auth/token/', credentials)
  return data
}

export async function refreshToken(refresh: string): Promise<RefreshTokenResponse> {
  const { data } = await httpClient.post<RefreshTokenResponse>('/auth/token/refresh/', { refresh })
  return data
}

export async function getMe(): Promise<MeResponse> {
  const { data } = await httpClient.get<MeResponse>('/auth/me/')
  return data
}

export async function logout(refresh: string): Promise<LogoutResponse> {
  const { data } = await httpClient.post<LogoutResponse>('/auth/logout/', { refresh })
  return data
}
