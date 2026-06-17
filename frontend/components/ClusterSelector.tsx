"use client";

import { useEffect, useState } from "react";
import { listClusters, ClusterContext } from "@/services/api";

interface Props {
  selectedContext: string | null;
  onSelect: (context: string) => void;
}

export default function ClusterSelector({ selectedContext, onSelect }: Props) {
  const [contexts, setContexts] = useState<ClusterContext[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    listClusters()
      .then((data) => {
        if (data.error) {
          setError(data.error);
        } else {
          setContexts(data.contexts);
          // Auto-select the current context
          if (!selectedContext) {
            const current = data.contexts.find((c) => c.is_current);
            if (current) onSelect(current.name);
            else if (data.contexts.length > 0) onSelect(data.contexts[0].name);
          }
        }
      })
      .catch(() => setError("Could not reach backend. Is it running?"))
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <span className="w-3 h-3 border border-gray-600 border-t-transparent rounded-full animate-spin" />
        Loading clusters…
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg px-4 py-3">
        {error}
      </div>
    );
  }

  if (contexts.length === 0) {
    return (
      <div className="text-sm text-gray-500 bg-gray-900 border border-gray-800 rounded-lg px-4 py-3">
        No Kubernetes contexts found in kubeconfig.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-gray-500 uppercase tracking-wide">
        Select Cluster
      </p>
      <div className="space-y-1.5">
        {contexts.map((ctx) => {
          const isSelected = selectedContext === ctx.name;
          return (
            <button
              key={ctx.name}
              onClick={() => onSelect(ctx.name)}
              className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                isSelected
                  ? "bg-blue-950 border-blue-600 text-white"
                  : "bg-gray-900 border-gray-800 text-gray-300 hover:border-gray-600"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">{ctx.name}</p>
                  {ctx.server && (
                    <p className="text-xs text-gray-500 truncate mt-0.5">
                      {ctx.server}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {ctx.is_current && (
                    <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded">
                      current
                    </span>
                  )}
                  {isSelected && (
                    <span className="text-blue-400 text-sm">✓</span>
                  )}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
