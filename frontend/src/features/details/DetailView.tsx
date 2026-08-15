import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  downloadPrivatePhoto,
  revokePrivateFile,
} from "../../api/privateFileApi";
import { getApiErrorKind } from "../../api/errors";
import type { ApiError, DetailPermissions } from "../../api/types";

export type DetailItem = {
  label: string;
  value?: string | number | boolean | null;
};

function PrivatePhoto({
  personaId,
  available,
  permissions,
  version,
}: {
  personaId: number;
  available?: boolean;
  permissions?: DetailPermissions;
  version?: string;
}) {
  const [url, setUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    if (!available || !permissions?.can_download_photo) return;
    let active = true;
    let createdUrl: string | null = null;
    void downloadPrivatePhoto(personaId)
      .then(({ url: objectUrl }) => {
        createdUrl = objectUrl;
        if (active) setUrl(objectUrl);
        else revokePrivateFile(objectUrl);
      })
      .catch(() => {
        if (active) setFailed(true);
      });
    return () => {
      active = false;
      revokePrivateFile(createdUrl);
    };
  }, [personaId, available, permissions?.can_download_photo, version]);
  if (!available || !permissions?.can_download_photo) return null;
  if (failed)
    return (
      <p className="detail-photo__unavailable" role="status" aria-live="polite">
        La foto no está disponible ahora.
      </p>
    );
  return url ? (
    <img className="detail-photo" src={url} alt="Foto de perfil autorizada" />
  ) : (
    <p role="status">Cargando foto…</p>
  );
}

type DetailViewProps = {
  title: string;
  eyebrow: string;
  backTo: string;
  backLabel: string;
  items: DetailItem[];
  isLoading: boolean;
  error: ApiError | null;
  onRetry: () => void;
  personaId?: number;
  photoAvailable?: boolean;
  photoVersion?: string;
  permissions?: DetailPermissions;
};

export function DetailView({
  title,
  eyebrow,
  backTo,
  backLabel,
  items,
  isLoading,
  error,
  onRetry,
  personaId,
  photoAvailable,
  photoVersion,
  permissions,
}: DetailViewProps) {
  if (isLoading)
    return (
      <article className="home-card detail-state" role="status">
        Cargando ficha…
      </article>
    );
  if (error) {
    const kind = getApiErrorKind(error);
    const heading =
      kind === "unauthorized"
        ? "Sesión no autorizada"
        : kind === "forbidden"
          ? "Acceso denegado"
          : kind === "not-found"
            ? "Ficha no encontrada"
            : "No fue posible cargar la ficha";
    return (
      <article className="home-card detail-state" role="alert">
        <h1>{heading}</h1>
        <p>
          {kind === "unauthorized"
            ? "Tu sesión ya no permite acceder a esta información. Inicia sesión nuevamente."
            : kind === "forbidden"
              ? "El backend no permite ver esta información."
              : kind === "not-found"
                ? "La ficha no existe o ya no está disponible."
                : error.error.message}
        </p>
        {kind === "other" ? (
          <button
            className="primary-button dashboard-retry-button"
            type="button"
            onClick={onRetry}
          >
            Reintentar
          </button>
        ) : null}
      </article>
    );
  }
  return (
    <section className="home-feed detail-page" aria-labelledby="detail-title">
      <Link className=" grupos-back-link" to={backTo}>
        Volver a {backLabel}
      </Link>
      <article className="home-card detail-card">
        <div>
          <p className="shell-panel-caption">{eyebrow}</p>
          <h1 id="detail-title">{title}</h1>
        </div>
        {personaId ? (
          <PrivatePhoto
            key={`${personaId}-${photoAvailable}-${photoVersion}-${permissions?.can_download_photo}`}
            personaId={personaId}
            available={photoAvailable}
            permissions={permissions}
            version={photoVersion}
          />
        ) : null}
        <dl className="detail-list">
          {items
            .filter(
              (item) =>
                item.value !== undefined &&
                item.value !== null &&
                item.value !== "",
            )
            .map((item) => (
              <div key={item.label}>
                <dt>{item.label}</dt>
                <dd>
                  {typeof item.value === "boolean"
                    ? item.value
                      ? "Sí"
                      : "No"
                    : item.value}
                </dd>
              </div>
            ))}
        </dl>
      </article>
    </section>
  );
}
