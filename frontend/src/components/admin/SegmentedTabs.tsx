interface SegmentedTab {
  key: string;
  label: string;
}

interface SegmentedTabsProps {
  tabs: SegmentedTab[];
  activeKey: string;
  onChange: (key: string) => void;
  compact?: boolean;
  equalWidth?: boolean;
}

const SegmentedTabs: React.FC<SegmentedTabsProps> = ({
  tabs,
  activeKey,
  onChange,
  compact = false,
  equalWidth = false,
}) => {
  return (
    <div
      className={`admin-tabs ${compact ? "admin-tabs-compact" : ""} ${equalWidth ? "admin-tabs-equal" : ""}`.trim()}
    >
      {tabs.map((tab) => (
        <button
          key={tab.key}
          type="button"
          onClick={() => onChange(tab.key)}
          className={`admin-tab ${activeKey === tab.key ? "admin-tab-active" : ""}`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
};

export default SegmentedTabs;
