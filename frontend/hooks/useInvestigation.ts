import { useQuery } from "@tanstack/react-query";
import apiClient from "@/services/api";

export function useHealthCheck() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => apiClient.get("/health").then((r) => r.data),
    enabled: false,
  });
}
