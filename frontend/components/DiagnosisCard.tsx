import { Diagnosis } from "@/types/investigation";

interface Props {
  diagnosis: Diagnosis;
}

export default function DiagnosisCard({ diagnosis }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4 text-left">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Diagnosis</h2>
        {diagnosis.confidence > 0 && (
          <span className="text-sm font-medium text-blue-400">
            {diagnosis.confidence}% confidence
          </span>
        )}
      </div>

      <div className="space-y-3">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
            Root Cause
          </p>
          <p className="text-white font-medium">{diagnosis.root_cause}</p>
        </div>

        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
            Explanation
          </p>
          <p className="text-gray-300 text-sm leading-relaxed">
            {diagnosis.explanation}
          </p>
        </div>

        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
            Suggested Fix
          </p>
          <p className="text-gray-300 text-sm leading-relaxed">
            {diagnosis.fix}
          </p>
        </div>

        {diagnosis.kubectl_commands && diagnosis.kubectl_commands.length > 0 && (
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">
              Commands
            </p>
            <div className="space-y-1">
              {diagnosis.kubectl_commands.map((cmd, i) => (
                <code
                  key={i}
                  className="block text-xs bg-gray-950 border border-gray-800 rounded px-3 py-2 text-green-400 font-mono"
                >
                  {cmd}
                </code>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
