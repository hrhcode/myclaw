interface StatusBadgeProps {
  tone?: "neutral" | "success" | "danger" | "warning" | "info";
  children: React.ReactNode;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ tone = "neutral", children }) => {
  return <span className={`admin-badge admin-badge-${tone}`}>{children}</span>;
};

export default StatusBadge;
