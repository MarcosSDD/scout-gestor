import type { ReactNode } from "react";

type PlaceholderPageProps = {
  eyebrow?: string;
  title: string;
  description: string;
  children?: ReactNode;
};

export function PlaceholderPage({
  eyebrow = "Proximamente",
  title,
  description,
  children,
}: PlaceholderPageProps) {
  return (
    <section className="home-feed" aria-label={title}>
      <article className="home-card home-card--hero">
        <p className="shell-panel-caption">{eyebrow}</p>
        <h1>{title}</h1>
        <p>{description}</p>
      </article>
      {children}
    </section>
  );
}
