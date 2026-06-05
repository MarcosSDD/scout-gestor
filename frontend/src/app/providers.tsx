import { QueryClientProvider } from '@tanstack/react-query'
import type { PropsWithChildren } from 'react'
import { BrowserRouter } from 'react-router-dom'
import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'

import '../api/authInterceptor'
import { AuthProvider } from '../features/auth/AuthProvider'
import { queryClient } from './queryClient'

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>{children}</AuthProvider>
        <ToastContainer position="top-right" autoClose={3500} />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
