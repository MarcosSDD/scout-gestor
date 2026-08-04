export const personasQueryKeys = {
  persona: (id: number) => ['personas', 'detail', id] as const,
  beneficiario: (id: number) => ['personas', 'beneficiarios', 'detail', id] as const,
  adulto: (id: number) => ['personas', 'adultos', 'detail', id] as const,
  unidades: (ramaId?: number, page = 1) => ['unidades', 'list', { ramaId, page }] as const,
  ramas: ['catalogos', 'ramas'] as const,
  progresiones: (beneficiario: number) => ['personas', 'progresiones', beneficiario] as const,
  progresion: (id: number) => ['personas', 'progresion', id] as const,
}
