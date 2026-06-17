export interface Diagnosis {
  root_cause: string;
  explanation: string;
  fix: string;
  kubectl_commands: string[];
  prevention: string;
  confidence: number;
  ai_available: boolean;
}

export interface InvestigationSummary {
  total_issues: number;
  cluster_healthy: boolean;
  issues: string[];
  errors: string[];
}

export interface InvestigationRequest {
  namespace?: string;
  context?: string;
  investigation_id?: string;
}

export interface InvestigationResponse {
  status: string;
  investigation_id?: string;
  investigation?: Record<string, unknown>;
  summary?: InvestigationSummary;
  diagnosis?: Diagnosis;
}
