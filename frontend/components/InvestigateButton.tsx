"use client";

import apiClient from "@/services/api";

type Status = "ready" | "investigating" | "done";

interface Props {
  status: Status;
  onStatusChange: (status: Status) => void;
}

export default function InvestigateButton({ status, onStatusChange }: Props) {
  const isLoading = status === "investigating";

  async function handleClick() {
    onStatusChange("investigating");
    try {
      await apiClient.get("/health");
      onStatusChange("done");
    } catch {
      onStatusChange("ready");
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={isLoading}
      className="w-full py-4 px-8 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-semibold text-lg transition-colors duration-200"
    >
      {isLoading ? "Investigating..." : "Investigate Cluster"}
    </button>
  );
}
