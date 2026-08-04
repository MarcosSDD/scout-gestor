import { describe, expect, it } from 'vitest'
import { asignacionSchema, personaSchema, progresionSchema } from './personasSchemas'

describe('esquemas de personas', () => {
  it('valida nombres y apellidos solamente si el formulario los incluye', () => expect(personaSchema.safeParse({ nombres: '', apellidos: '', email: '' }).success).toBe(false))
  it('exige una unidad válida en la asignación', () => expect(asignacionSchema.safeParse({ rama_actual: 2, unidad: 0 }).success).toBe(false))
  it('requiere texto y al menos un área de progresión', () => expect(progresionSchema.safeParse({ beneficiario: 3, fecha: '2025-01-01', tipo: 'DURANTE_CICLO', texto: '', areas: [] }).success).toBe(false))
  it('rechaza fechas futuras de progresión', () => expect(progresionSchema.safeParse({ beneficiario: 3, fecha: '2999-01-01', tipo: 'DURANTE_CICLO', texto: 'Participó activamente.', areas: [1] }).success).toBe(false))
  it('acepta fotos JPG, PNG y WebP de hasta 2 MB', () => {
    expect(personaSchema.safeParse({ email: '', foto: { name: 'perfil.webp', type: 'image/webp', size: 4 } as File }).success).toBe(true)
    expect(personaSchema.safeParse({ email: '', foto: { name: 'perfil.jpg', type: 'application/octet-stream', size: 4 } as File }).success).toBe(true)
  })
  it('rechaza fotos con formato o tamaño inválido', () => {
    expect(personaSchema.safeParse({ email: '', foto: { name: 'perfil.gif', type: 'image/gif', size: 4 } as File }).success).toBe(false)
    expect(personaSchema.safeParse({ email: '', foto: { name: 'perfil.png', type: 'image/png', size: 2 * 1024 * 1024 + 1 } as File }).success).toBe(false)
  })
})
