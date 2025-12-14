type DaySelectorProps = {
  value: string;
  onChange: (date: string) => void;
};

export function DaySelector({ value, onChange }: DaySelectorProps) {
  return (
    <div>
      <label>
        Select date:
        <input
          type="date"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      </label>
    </div>
  );
}
