interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  ariaLabel: string;
}

const Switch: React.FC<SwitchProps> = ({ checked, onChange, ariaLabel }) => {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`admin-switch ${checked ? "admin-switch-on" : ""}`}
      aria-label={ariaLabel}
      aria-pressed={checked}
    >
      <span className={`admin-switch-thumb ${checked ? "admin-switch-thumb-on" : ""}`} />
    </button>
  );
};

export default Switch;
