import type { ReactNode } from "react";

interface SectionCardProps {
  children: ReactNode;
  className?: string;
}

const SectionCard: React.FC<SectionCardProps> = ({ children, className }) => {
  return <div className={`admin-card ${className || ""}`.trim()}>{children}</div>;
};

export default SectionCard;
