const STEPS = [
  "Checking Pods",
  "Reading Logs",
  "Analyzing Events",
  "Inspecting Deployments",
  "Checking Networking",
  "AI Reasoning",
];

type StepStatus = "pending" | "running" | "done";

interface Props {
  completedSteps: Set<string>;
  activeStep: string | null;
}

export default function ProgressSteps({ completedSteps, activeStep }: Props) {
  function getStatus(step: string): StepStatus {
    if (completedSteps.has(step)) return "done";
    if (activeStep === step) return "running";
    return "pending";
  }

  return (
    <div className="space-y-2">
      {STEPS.map((step) => {
        const status = getStatus(step);
        return (
          <div key={step} className="flex items-center gap-3 text-sm">
            <span className="w-5 text-center flex-shrink-0">
              {status === "done" && (
                <span className="text-green-400">✓</span>
              )}
              {status === "running" && (
                <span className="text-yellow-400 animate-pulse">⟳</span>
              )}
              {status === "pending" && (
                <span className="text-gray-700">○</span>
              )}
            </span>
            <span
              className={
                status === "done"
                  ? "text-gray-300"
                  : status === "running"
                  ? "text-yellow-400"
                  : "text-gray-600"
              }
            >
              {step}
            </span>
          </div>
        );
      })}
    </div>
  );
}
