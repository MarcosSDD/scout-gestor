import { httpClient } from './httpClient'
import type { ApiSuccess } from './types'

export type HealthData = {
  status: 'ok'
  version: string
}

export type HealthResponse = ApiSuccess<HealthData>

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await httpClient.get<HealthResponse>('/health/')
  return data
}
