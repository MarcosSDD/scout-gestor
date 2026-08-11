import { z } from 'zod'

const id = z.number().int().positive('Selecciona una opción válida.')
export const unidadSchema = z.object({ grupo: id, rama: id, nombre: z.string().trim().min(1, 'Indica el nombre.').max(120), tipo_composicion: z.string().trim().max(20), estado: z.enum(['ACTIVA', 'INACTIVA']), cupo_maximo: z.number().int().positive().nullable() })
export const subgrupoSchema = z.object({ unidad: id, nombre: z.string().trim().min(1, 'Indica el nombre.').max(100), lider_juvenil: z.number().int().positive().nullable() })
export const miembroSchema = z.object({ subgrupo: id, beneficiario: id })
export const reasignacionSchema = z.object({ subgrupo: id })
export const adultoUnidadSchema = z.object({ unidad: id, adulto: id, rol: z.enum(['RESPONSABLE', 'ASISTENTE', 'COLABORADOR']) })
export type UnidadFormValues = z.output<typeof unidadSchema>
export type SubgrupoFormValues = z.output<typeof subgrupoSchema>
export type MiembroFormValues = z.output<typeof miembroSchema>
export type ReasignacionFormValues = z.output<typeof reasignacionSchema>
export type AdultoUnidadFormValues = z.output<typeof adultoUnidadSchema>
