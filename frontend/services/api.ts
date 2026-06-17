import axios from "axios";
import { InvestigationRequest, InvestigationResponse } from "@/types/investigation";

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 120000,
});

export interface ClusterContext {
  name: string;
  cluster: string;
  server: string;
  is_current: boolean;
}

export interface ClustersResponse {
  contexts: ClusterContext[];
  current_context: string | null;
  error?: string;
}

export async function listClusters(): Promise<ClustersResponse> {
  const { data } = await apiClient.get<ClustersResponse>("/clusters");
  return data;
}

export async function runInvestigation(
  request: InvestigationRequest = {}
): Promise<InvestigationResponse> {
  const { data } = await apiClient.post<InvestigationResponse>(
    "/investigate",
    request
  );
  return data;
}

export default apiClient;
