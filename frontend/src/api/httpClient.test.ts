import { httpClient } from './httpClient'

describe('httpClient', () => {
  it('uses api v1 base URL by default', () => {
    expect(httpClient.defaults.baseURL).toBe('/api/v1')
  })

  it('sets json headers and timeout', () => {
    expect(httpClient.defaults.timeout).toBe(15000)
    expect(httpClient.defaults.headers.Accept).toBe('application/json')

    const contentType = httpClient.defaults.headers['Content-Type'] as string
    expect(contentType).toBe('application/json')
  })
})
