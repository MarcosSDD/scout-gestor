import type { FieldValues, Path, UseFormSetError } from "react-hook-form";

type DrfDetails = Record<string, unknown>;

function messages(value: unknown): string[] {
  if (typeof value === "string") return [value];
  if (Array.isArray(value)) return value.flatMap(messages);
  if (value && typeof value === "object")
    return Object.values(value).flatMap(messages);
  return ["El valor no es válido."];
}

/** Maps only declared form fields; all other DRF errors are safe global messages. */
export function applyDrfErrors<T extends FieldValues>(
  details: unknown,
  setError: UseFormSetError<T>,
  allowedFields: readonly Path<T>[],
): string[] {
  if (!details || typeof details !== "object" || Array.isArray(details))
    return messages(details);
  const allowed = new Set<string>(allowedFields);
  const globalErrors: string[] = [];
  for (const [field, value] of Object.entries(details as DrfDetails)) {
    const fieldMessages = messages(value);
    if (
      allowed.has(field) &&
      !(value && typeof value === "object" && !Array.isArray(value))
    ) {
      setError(field as Path<T>, {
        type: "server",
        message: fieldMessages.join(" "),
      });
    } else {
      globalErrors.push(...fieldMessages);
    }
  }
  return globalErrors;
}
