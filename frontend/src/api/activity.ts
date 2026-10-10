import { apiClient, API_BASE, USE_FIXTURES } from './client';
import type { ActivityBatch, ActivityEvents, ActivitySummary } from './types';
export interface ActivityReceipt { received: number; last_seq: number }
export const postActivity = (submissionId: string, batch: ActivityBatch) => apiClient<ActivityReceipt>(`/submissions/${encodeURIComponent(submissionId)}/activity`, { method: 'POST', body: JSON.stringify(batch) });
export const activityApi = {
  events: (submissionId: string) => apiClient<ActivityEvents>(`/submissions/${encodeURIComponent(submissionId)}/activity/events`, { fixtureName: `activity_events_${submissionId.replaceAll('_', '')}` }),
  summary: (submissionId: string) => apiClient<ActivitySummary>(`/submissions/${encodeURIComponent(submissionId)}/activity/summary`, { fixtureName: `activity_summary_${submissionId.replaceAll('_', '')}` }),
};
export function sendActivityOnExit(submissionId: string, batch: ActivityBatch): void {
  if (USE_FIXTURES) { void postActivity(submissionId, batch).catch(() => {}); return; }
  const url = `${API_BASE}/submissions/${encodeURIComponent(submissionId)}/activity`;
  // Beacon cannot set X-User-Id. Keep the local batch until an authenticated retry succeeds.
  navigator.sendBeacon(url, new Blob([JSON.stringify(batch)], { type: 'application/json' }));
  void fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-User-Id': localStorage.getItem('currentUserId') || '' }, body: JSON.stringify(batch), keepalive: true }).catch(() => {});
}
