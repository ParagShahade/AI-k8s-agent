"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { insforge } from "@/lib/insforge";
import { useAuth } from "@/lib/auth-context";

function VerifyEmailForm() {
  const router = useRouter();
  const { setUser } = useAuth();
  const params = useSearchParams();
  const email = params.get("email") || "";

  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const { data, error } = await insforge.auth.verifyEmail({ email, otp });

    setLoading(false);

    if (error) {
      setError(error.message || "Invalid code");
      return;
    }

    if (data?.user) {
      setUser(data.user as Parameters<typeof setUser>[0]);
      router.push("/");
    }
  }

  async function handleResend() {
    await insforge.auth.resendVerificationEmail({ email });
  }

  return (
    <main className="min-h-screen bg-gray-950 text-white flex items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold">Check your email</h1>
          <p className="text-gray-400 text-sm">
            We sent a 6-digit code to{" "}
            <span className="text-white">{email}</span>
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-sm text-gray-400">Verification Code</label>
            <input
              type="text"
              required
              maxLength={6}
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
              className="w-full px-4 py-3 rounded-lg bg-gray-900 border border-gray-800 text-white text-center text-xl tracking-widest placeholder-gray-600 focus:outline-none focus:border-blue-500"
              placeholder="000000"
            />
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={loading || otp.length < 6}
            className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-blue-900 disabled:cursor-not-allowed font-semibold transition-colors"
          >
            {loading ? "Verifying..." : "Verify Email"}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500">
          Didn&apos;t receive it?{" "}
          <button
            onClick={handleResend}
            className="text-blue-400 hover:text-blue-300"
          >
            Resend code
          </button>
        </p>
      </div>
    </main>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense>
      <VerifyEmailForm />
    </Suspense>
  );
}
