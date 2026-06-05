import { Icon } from './Icon'

type MobileSearchOverlayProps = {
  isOpen: boolean
  onClose: () => void
}

export function MobileSearchOverlay({ isOpen, onClose }: MobileSearchOverlayProps) {
  return (
    <div className={`shell-mobile-search ${isOpen ? 'show' : ''}`}>
      <form className="shell-mobile-search__form" role="search">
        <Icon name="search" />
        <input type="search" placeholder="Buscar..." aria-label="Buscar" />
        <button type="button" onClick={onClose} aria-label="Cerrar busqueda">x</button>
      </form>
    </div>
  )
}
