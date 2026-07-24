import { useEffect, useRef } from 'react'

import { Icon } from './Icon'

type MobileSearchOverlayProps = {
  isOpen: boolean
  onClose: () => void
}

export function MobileSearchOverlay({ isOpen, onClose }: MobileSearchOverlayProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!isOpen) return undefined
    inputRef.current?.focus()
    const onKeyDown = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="shell-mobile-search show" role="dialog" aria-modal="true" aria-label="Busqueda">
      <form className="shell-mobile-search__form" role="search">
        <Icon name="search" />
        <input ref={inputRef} type="search" placeholder="Buscar..." aria-label="Buscar" />
        <button type="button" onClick={onClose} aria-label="Cerrar busqueda">x</button>
      </form>
    </div>
  )
}
