export type PaginatedMeta = {
  count: number
  next: string | null
  previous: string | null
  page?: number
  page_size?: number
}

export type ApiSuccess<TData, TMeta = unknown> = {
  success: true
  message: string
  data: TData
  meta?: TMeta
}

export type ApiError = {
  success: false
  error: {
    code: string
    message: string
    details: unknown
  }
}
