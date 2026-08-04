import { httpClient } from './httpClient'
import { toApiError } from './errors'

function filenameFromDisposition(value?: string) {
  const encoded = value?.match(/filename\*=UTF-8''([^;]+)/i)?.[1]
  const plain = value?.match(/filename="?([^";]+)"?/i)?.[1]
  try { return encoded ? decodeURIComponent(encoded) : plain } catch { return plain }
}

export async function downloadPrivatePhoto(personaId: number) {
  return downloadPrivateFile(`/personas/${personaId}/foto/`)
}

export async function downloadPrivateFile(path: string) {
  try {
    const response = await httpClient.get(path, { responseType: 'blob' })
    return { url: URL.createObjectURL(response.data), filename: filenameFromDisposition(response.headers['content-disposition']) }
  } catch (error) {
    if (typeof Blob !== 'undefined' && (error as { response?: { data?: unknown } }).response?.data instanceof Blob) {
      const response = (error as { response: { data: Blob } }).response
      try { response.data = JSON.parse(await response.data.text()) } catch { /* preserve the original error */ }
    }
    throw toApiError(error)
  }
}

export function revokePrivateFile(url?: string | null) {
  if (url) URL.revokeObjectURL(url)
}
