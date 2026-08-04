type SessionExpiredListener = () => void

const listeners = new Set<SessionExpiredListener>()
let notified = false

/** Framework-independent bridge used by the Axios interceptor. */
export function notifySessionExpired() {
  if (notified) return
  notified = true
  listeners.forEach((listener) => listener())
}

export function resetSessionExpiredNotification() {
  notified = false
}

export function subscribeToSessionExpired(listener: SessionExpiredListener) {
  listeners.add(listener)
  return () => { listeners.delete(listener) }
}
