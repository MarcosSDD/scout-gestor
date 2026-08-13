import { z } from "zod";

const optionalText = z.string().trim().max(200).optional();
const photoMimeTypes = new Set(["image/jpeg", "image/png", "image/webp"]);
const photoExtension = /\.(?:jpe?g|png|webp)$/i;
const fotoSchema = z
  .custom<File>(
    (value): value is File =>
      Boolean(
        value &&
          typeof value === "object" &&
          "name" in value &&
          "size" in value &&
          "type" in value,
      ),
    "Selecciona una imagen válida.",
  )
  .refine(
    (file) => photoMimeTypes.has(file.type) || photoExtension.test(file.name),
    "La foto debe ser JPG, PNG o WebP.",
  )
  .refine(
    (file) => file.size <= 2 * 1024 * 1024,
    "La foto no puede superar 2 MB.",
  );
export const personaSchema = z.object({
  nombres: z.string().trim().min(1, "Ingresa los nombres.").max(100).optional(),
  apellidos: z
    .string()
    .trim()
    .min(1, "Ingresa los apellidos.")
    .max(100)
    .optional(),
  fecha_nacimiento: z.string().optional(),
  sexo: z.string().optional(),
  direccion: optionalText,
  telefono: optionalText,
  email: z.union([z.literal(""), z.email("Ingresa un correo válido.")]),
  estado: z.enum(["ACTIVO", "INACTIVO"]).optional(),
  foto: fotoSchema.optional(),
});
export const beneficiarioSchema = z.object({
  fecha_ingreso: z.string().min(1, "Indica la fecha de ingreso."),
});
export const asignacionSchema = z.object({
  unidad: z.number().int().positive("Selecciona una unidad."),
  rama_actual: z.number().int().positive("Selecciona una rama."),
});
export const certificadoSchema = z.object({
  certificado_vigencia_hasta: z.string().min(1, "Indica la vigencia."),
  certificado_inhabilidades: z
    .instanceof(File, { message: "Adjunta el certificado en PDF." })
    .refine(
      (file) => file.type === "application/pdf",
      "El certificado debe ser un PDF.",
    )
    .refine(
      (file) => file.size <= 5 * 1024 * 1024,
      "El certificado no puede superar 5 MB.",
    ),
});
const today = () => new Date().toISOString().slice(0, 10);
export const progresionSchema = z.object({
  beneficiario: z.number().int().positive(),
  fecha: z
    .string()
    .min(1, "Indica la fecha.")
    .refine((date) => date <= today(), "La fecha no puede ser futura."),
  tipo: z.enum(["INICIO_CICLO", "DURANTE_CICLO", "FINAL_CICLO"]),
  texto: z.string().trim().min(1, "Describe el avance observado.").max(4000),
  areas: z
    .array(z.number().int().positive())
    .min(1, "Selecciona al menos un área."),
});

export type PersonaFormValues = z.input<typeof personaSchema>;
export type BeneficiarioFormValues = z.output<typeof beneficiarioSchema>;
export type AsignacionFormValues = z.output<typeof asignacionSchema>;
export type CertificadoFormValues = z.output<typeof certificadoSchema>;
export type ProgresionFormValues = z.output<typeof progresionSchema>;
