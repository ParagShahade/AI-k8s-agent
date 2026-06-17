"use client";

import { useEffect, useState } from "react";
import { insforge } from "@/lib/insforge";

interface HistoryItem {
  id: string;
  root_cause: string;
  namespace: string;
  confidence: number;
  status: string;
  created_at: string;
}

interface Props {
  refreshKey: number;
}

export default function InvestigationHistory({ refreshKey }: Props) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    insforge.database
      .from("investigation_history")
      .select("id, root_cause, namespace, confidence, status, created_at")
      .order("created_at", { ascending: false })
      .limit(10)
      .then(({ data }) => {
        setItems((data as HistoryItem[]) ?? []);
        setLoading(false);
      });
  }, [refreshKey]);

  if (loading) {
    return <p className="text-gray-600 text-sm">Loading history...</p>;
  }

  if (items.length === 0) {
    return (
      <p className="text-gray-600 text-sm">No investigations yet.</p>
    );
  }

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div
          key={item.id}
          className="flex items-center justify-between bg-gray-900 border border-gray-800 rounded-lg px-4 py-3"
        >
          <div className="text-left min-w-0">
            <p className="text-sm text-white truncate">
              {item.root_cause || "Unknown"}
            </p>
            <p className="text-xs text-gray-500">
              {item.namespace} ·{" "}
              {new Date(item.created_at).toLocaleDateString()}
            </p>
          </div>
          {item.confidence > 0 && (
            <span className="text-xs text-gray-500 flex-shrink-0 ml-3">
              {item.confidence}%
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
