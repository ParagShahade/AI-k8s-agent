"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { insforge } from "@/lib/insforge";
import { runInvestigation } from "@/services/api";
import ClusterSelector from "@/components/ClusterSelector";
import ProgressSteps from "@/components/ProgressSteps";
import DiagnosisCard from "@/components/DiagnosisCard";
import InvestigationHistory from "@/components/InvestigationHistory";
import { Diagnosis } from "@/types/investigation";

type AppState = "idle" | "investigating" | "done" | "error";

function friendlyError(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const resp = (err as { response?: { data?: { detail?: string } } }).response;
    const detail = resp?.data?.detail;
    if (detail) return detail;
  }
  if (err instanceof Error) return err.message;
  return "Something went wrong. Please try again.";
}

export default function DashboardPage() {
  const { user, loading, signOut } = useAuth();
  const router = useRouter();

  const [appState, setAppState] = useState<AppState>("idle");
  const [selectedContext, setSelectedContext] = useState<string | null>(null);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());
  const [activeStep, setActiveStep] = useState<string | null>(null);
  const [diagnosis, setDiagnosis] = useState<Diagnosis | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [historyKey, setHistoryKey] = useState(0);

  const realtimeConnected = useRef(false);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  async function handleInvestigate() {
    if (!user || !selectedContext) return;

    setAppState("investigating");
    setCompletedSteps(new Set());
    setActiveStep(null);
    setDiagnosis(null);
    setErrorMsg("");

    const investigationId = crypto.randomUUID();

    // Subscribe to realtime progress before calling the API
    try {
      if (!realtimeConnected.current) {
        await insforge.realtime.connect();
        realtimeConnected.current = true;
      }
      await insforge.realtime.subscribe(`investigation:${investigationId}`);
      insforge.realtime.on(
        "progress",
        (payload: { step: string; done: boolean }) => {
          if (payload.done) {
            setCompletedSteps((prev) => new Set(prev).add(payload.step));
            setActiveStep(null);
          } else {
            setActiveStep(payload.step);
          }
        }
      );
    } catch (err) {
      // Non-fatal — investigation still runs, just no live progress
      console.warn("Realtime subscription failed:", err);
    }

    try {
      const result = await runInvestigation({
        namespace: "all",
        context: selectedContext,
        investigation_id: investigationId,
      });

      if (result.diagnosis) {
        setDiagnosis(result.diagnosis);
        setAppState("done");

        // Save to InsForge history
        await insforge.database.from("investigation_history").insert([
          {
            user_id: user.id,
            namespace: "all",
            root_cause: result.diagnosis.root_cause,
            explanation: result.diagnosis.explanation,
            fix: result.diagnosis.fix,
            kubectl_commands: result.diagnosis.kubectl_commands,
            confidence: result.diagnosis.confidence,
            status: "completed",
          },
        ]);
        setHistoryKey((k) => k + 1);
      } else {
        setErrorMsg("Investigation returned no diagnosis.");
        setAppState("error");
      }
    } catch (err) {
      setErrorMsg(friendlyError(err));
      setAppState("error");
    } finally {
      try {
        await insforge.realtime.unsubscribe(`investigation:${investigationId}`);
      } catch {}
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </main>
    );
  }

  if (!user) return null;

  const isHealthy =
    appState === "done" &&
    diagnosis &&
    /health|no issue|no critical|no problem/i.test(diagnosis.root_cause);

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-900 px-6 py-4 flex items-center justify-between">
        <span className="font-semibold text-sm">AI Kubernetes Agent</span>
        <div className="flex items-center gap-4">
          <span className="text-xs text-gray-500">{user.email}</span>
          <button
            onClick={async () => {
              await signOut();
              router.push("/login");
            }}
            className="text-xs text-gray-500 hover:text-white transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      <div className="max-w-lg mx-auto px-4 py-10 space-y-8">
        {/* Title */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold tracking-tight">
            AI Kubernetes Agent
          </h1>
          <p className="text-gray-400">
            Select a cluster and get an AI-powered diagnosis.
          </p>
        </div>

        {/* Cluster selector */}
        <ClusterSelector
          selectedContext={selectedContext}
          onSelect={setSelectedContext}
        />

        {/* Investigate button */}
        <button
          onClick={handleInvestigate}
          disabled={appState === "investigating" || !selectedContext}
          className="w-full py-4 px-8 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-blue-900 disabled:cursor-not-allowed text-white font-semibold text-lg transition-colors"
        >
          {appState === "investigating"
            ? "Investigating…"
            : "Investigate Cluster"}
        </button>

        {/* Progress */}
        {(appState === "investigating" || appState === "done") && (
          <div className="space-y-3">
            <h2 className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Investigation Progress
            </h2>
            <ProgressSteps
              completedSteps={completedSteps}
              activeStep={activeStep}
            />
          </div>
        )}

        {/* Error */}
        {appState === "error" && (
          <div className="bg-gray-900 border border-red-900 rounded-xl p-5 space-y-2">
            <p className="text-red-400 font-medium text-sm">
              Investigation failed
            </p>
            <p className="text-gray-300 text-sm whitespace-pre-line leading-relaxed">
              {errorMsg}
            </p>
          </div>
        )}

        {/* Healthy cluster banner */}
        {isHealthy && (
          <div className="bg-green-950 border border-green-800 rounded-xl px-5 py-4 flex items-center gap-3">
            <span className="text-green-400 text-xl">✓</span>
            <div>
              <p className="text-green-300 font-medium text-sm">
                Cluster appears healthy
              </p>
              <p className="text-green-600 text-xs mt-0.5">
                No critical issues were detected.
              </p>
            </div>
          </div>
        )}

        {/* Diagnosis */}
        {diagnosis && appState === "done" && (
          <DiagnosisCard diagnosis={diagnosis} />
        )}

        {/* History */}
        <div className="space-y-3">
          <h2 className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Previous Investigations
          </h2>
          <InvestigationHistory refreshKey={historyKey} />
        </div>
      </div>
    </main>
  );
}
