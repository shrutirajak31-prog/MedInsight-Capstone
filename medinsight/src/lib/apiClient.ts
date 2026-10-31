export type ApiFinding = {
  id: string;
  name: string;
  value: number;
  unit: string;
  referenceRange: string;
  status: 'Normal' | 'High' | 'Low';
  extractedSpan?: { page: number; text: string; bbox: [number, number, number, number] };
  explanation?: string;
  sources?: Array<{ source: string; title: string; url?: string; publication?: string }>;
};

export type ApiReport = {
  reportId: string;
  filename: string;
  status: 'uploaded' | 'processing' | 'ready' | 'error';
  summary?: string;
  extractedText?: string;
  findings?: ApiFinding[];
};

export type TrendPoint = { date: string; metric: string; value: number; unit: string };
export type EvidenceResponse = { findingId: string; sources: ApiFinding['sources']; edges: Array<{ from: string; to: string; type: string }> };

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
  });
  if (!response.ok) throw new Error(`MedInsight API request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

/** Replace demoData.ts with these calls once the FastAPI routes are available. */
export const apiClient = {
  checkHealth() {
    return fetch(`${API_BASE}/docs`, { method: 'GET' }).then((response) => {
      if (!response.ok) throw new Error('Backend health check failed');
      return true;
    });
  },
  uploadReport(file: File) {
    const body = new FormData();
    body.append('file', file);
    return fetch(`${API_BASE}/reports/upload`, { method: 'POST', body }).then(async (response) => {
      if (!response.ok) throw new Error(`Upload failed: ${response.status}`);
      return response.json() as Promise<ApiReport>;
    });
  },
  getReport(reportId: string) { return request<ApiReport>(`/reports/${encodeURIComponent(reportId)}`); },
  getTrend(patientId: string, metric: string) { return request<TrendPoint[]>(`/patients/${encodeURIComponent(patientId)}/trends?metric=${encodeURIComponent(metric)}`); },
  getEvidence(findingId: string) { return request<EvidenceResponse>(`/evidence/${encodeURIComponent(findingId)}`); },
  askQuestion(reportId: string, question: string, locale = 'en') { return request<{ answer: string; sources?: ApiFinding['sources']; evidenceSufficient: boolean }>(`/reports/${encodeURIComponent(reportId)}/questions`, { method: 'POST', body: JSON.stringify({ question, locale }) }); },
  reviewFinding(findingId: string, verdict: 'correct' | 'needs_review', note?: string) { return request<{ saved: boolean }>(`/reviews/${encodeURIComponent(findingId)}`, { method: 'POST', body: JSON.stringify({ verdict, note }) }); },
};
