import { adultoUnidadSchema, miembroSchema, subgrupoSchema, unidadSchema } from './structuralSchemas'

describe('structural schemas', () => {
  it('requires structural context and valid values', () => {
    expect(unidadSchema.safeParse({ grupo: 0, rama: 2, nombre: '', tipo_composicion: '', estado: 'ACTIVA', cupo_maximo: null }).success).toBe(false)
    expect(subgrupoSchema.safeParse({ unidad: 1, nombre: 'Patrulla A', lider_juvenil: null }).success).toBe(true)
    expect(miembroSchema.safeParse({ subgrupo: 2, beneficiario: 3 }).success).toBe(true)
    expect(adultoUnidadSchema.safeParse({ unidad: 1, adulto: 2, rol: 'OTRO' }).success).toBe(false)
  })
})
