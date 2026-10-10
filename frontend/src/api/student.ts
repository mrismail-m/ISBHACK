import { apiClient } from './client';
import type { Assessment, StudentResult, Submission, User } from './types';
const id = encodeURIComponent;
export const studentApi = {
  users: () => apiClient<User[]>('/users', { fixtureName: 'users' }),
  assessments: () => apiClient<Assessment[]>('/assessments?status=open', { fixtureName: 'assessments' }),
  assessment: (assessmentId: string) => apiClient<Assessment>(`/assessments/${id(assessmentId)}`, { fixtureName: `assessment_${assessmentId.replaceAll('_', '')}` }),
  start: (assessmentId: string) => apiClient<Submission>(`/assessments/${id(assessmentId)}/submissions`, { method: 'POST' }),
  save: (submissionId: string, content_md: string) => apiClient<Submission>(`/submissions/${id(submissionId)}`, { method: 'PUT', body: JSON.stringify({ content_md }) }),
  submit: (submissionId: string) => apiClient<Submission>(`/submissions/${id(submissionId)}/submit`, { method: 'POST' }),
  result: (submissionId: string) => apiClient<StudentResult>(`/submissions/${id(submissionId)}/result`, { fixtureName: `result_${submissionId.replaceAll('_', '')}` }),
};
