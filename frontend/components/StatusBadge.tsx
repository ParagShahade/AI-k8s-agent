type Status = "ready" | "investigating" | "done";

const config: Record<Status, { label: string; color: string; dot: string }> = {
  ready: {
    label: "Ready",
    color: "text-green-400",
    dot: "bg-green-400",
  },
  investigating: {
    label: "Investigating",
    color: "text-yellow-400",
    dot: "bg-yellow-400 animate-pulse",
  },
  done: {
    label: "Complete",
    color: "text-blue-400",
    dot: "bg-blue-400",
  },
};

export default function StatusBadge({ status }: { status: Status }) {
  const { label, color, dot } = config[status];

  return (
    <span className={`flex items-center gap-1.5 font-medium ${color}`}>
      <span className={`w-2 h-2 rounded-full ${dot}`} />
      {label}
    </span>
  );
}
