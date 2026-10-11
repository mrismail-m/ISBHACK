import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { demoRequest } from './demo-store';
import type { Submission } from '../../api/types';

beforeEach(() => {
  const data = new Map<string, string>([['currentUserId', 'u_student_3']]);
  vi.stubGlobal('localStorage', {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => { data.set(key, value); },
  });
});
afterEach(() => vi.unstubAllGlobals());
it('opens A2, saves and submits it, then resumes the same locked assignment', () => {
  const start = () => demoRequest('/assessments/a_write/submissions', { method: 'POST' }) as Submission;
  const first = start();
  expect(first.assessment_id).toBe('a_write');
  expect(first.status).toBe('draft');
  demoRequest(`/submissions/${first.id}`, { method: 'PUT', body: JSON.stringify({ content_md: 'Hash collisions use chaining.' }) });
  const submitted = demoRequest(`/submissions/${first.id}/submit`, { method: 'POST' }) as Submission;
  expect(submitted.status).toBe('submitted');
  expect(start()).toEqual(submitted);
  expect(() => demoRequest(`/submissions/${first.id}`, { method: 'PUT', body: '{}' })).toThrow('already submitted');
});
it('preserves A1 IDs and isolates work by assessment and student', () => {
  const first = demoRequest('/assessments/a_1/submissions', { method: 'POST' }) as Submission;
  const second = demoRequest('/assessments/a_write/submissions', { method: 'POST' }) as Submission;
  expect(first.id).toBe('s_demo_u_student_3');
  expect(second.id).not.toBe(first.id);
  localStorage.setItem('currentUserId', 'u_student_4');
  const other = demoRequest('/assessments/a_write/submissions', { method: 'POST' }) as Submission;
  expect(other.id).not.toBe(second.id);
  expect(() => demoRequest('/assessments/demo_a_1/submissions', { method: 'POST' })).toThrow('not open');
  expect(() => demoRequest('/assessments/unknown/submissions', { method: 'POST' })).toThrow('not found');
});
