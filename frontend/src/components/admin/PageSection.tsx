import type { ReactNode } from "react";

interface PageSectionProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  tight?: boolean;
  hideHeader?: boolean;
}

const PageSection: React.FC<PageSectionProps> = ({
  title,
  description,
  actions,
  children,
  tight = false,
  hideHeader = false,
}) => {
  return (
    <section className={`admin-section ${tight ? "admin-section-tight" : ""}`}>
      {!hideHeader && (
        <div className="admin-section-head">
          <div>
            <h2 className="admin-section-title">{title}</h2>
            {description ? <p className="admin-section-description">{description}</p> : null}
          </div>
          {actions ? <div>{actions}</div> : null}
        </div>
      )}
      {children}
    </section>
  );
};

export default PageSection;
