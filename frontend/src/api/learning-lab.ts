import { apiClient, ApiError, USE_FIXTURES } from './client';
import { studentApi } from './student';
import type { LabObservation, LabReport, LabState } from './types';
import plan from '../../../fixtures/api/llm/lab_plan.json';

const prefix = 'vivagrade:learning-lab:v1:';
const storageKey = (id: string) => `${prefix}${id}`;
function read(id: string): LabState | null {
  try { return JSON.parse(localStorage.getItem(storageKey(id)) || 'null') as LabState | null; }
  catch { return null; }
}
function write(value: LabState): LabState {
  localStorage.setItem(storageKey(value.submission_id), JSON.stringify(value));
  return value;
}
function fixtureObservation(answer: string): LabObservation {
  const text = answer.toLowerCase();
  const mechanism = ['chain', 'bucket', 'collision', 'probe'].some(word => text.includes(word));
  const cost = ['linear', 'o(n)', 'scan', 'every', 'all keys'].some(word => text.includes(word));
  const level = mechanism && cost ? 2 : mechanism || cost ? 1 : 0;
  return {
    level, answer_quote: answer.slice(0, 160),
    reasoning: level === 2 ? 'The response connects collisions to a linear search.'
      : 'The response does not yet connect bucket crowding to the number of entries searched.',
    suspected_gap: level === 2 ? '' : 'Average lookup versus worst-case lookup',
    teaching: 'A hash picks a bucket; it does not eliminate searching inside it. If n entries share a bucket, lookup may scan n entries, so it is O(n). Resizing only helps if the new mapping actually spreads those entries. Check the distribution, not just the table size.',
  };
}
export const labApi = {
  async get(id: string): Promise<LabState | null> {
    if (USE_FIXTURES) { await studentApi.submission(id); return read(id); }
    try { return await apiClient<LabState>(`/submissions/${id}/learning-lab`); }
    catch (error) { if (error instanceof ApiError && error.status === 404) return null; throw error; }
  },
  async start(id: string): Promise<LabState> {
    if (!USE_FIXTURES) return apiClient(`/submissions/${id}/learning-lab/start`, { method: 'POST' });
    const submission = await studentApi.submission(id);
    const saved = read(id);
    if (saved) return saved;
    if (submission.status === 'draft' || !submission.content_md.trim()) throw new Error('Submit your written assignment before starting the Learning Lab.');
    if (!['hash', 'collision', 'chaining', 'open addressing'].some(term => submission.content_md.toLowerCase().includes(term))) throw new Error('The offline fixture supports hash-table submissions only.');
    return write({
      id: `lab_${id}`, submission_id: id, assessment_id: submission.assessment_id,
      concept: plan.concept, anchor_quote: (submission.content_md.split('\n').map(line => line.trim()).find(line => line.length > 15 && !line.startsWith('#')) || submission.content_md.trim()).slice(0, 160),
      phase: 'challenge', challenge: plan.challenge, recovery: null,
      initial_answer: '', recovery_answer: '', initial: null, final: null,
      mode: 'fixture', created_at: new Date().toISOString(),
    });
  },
  async answer(id: string, phase: 'challenge' | 'recovery', answer: string): Promise<LabState> {
    if (!USE_FIXTURES) return apiClient(`/submissions/${id}/learning-lab/answer`, {
      method: 'POST', body: JSON.stringify({ phase, answer_text: answer }),
    });
    await studentApi.submission(id);
    const state = read(id);
    if (!state) throw new Error('Start the Learning Lab first.');
    const text = answer.trim();
    if (!text || text.length > 3000) throw new Error('Write an answer of up to 3,000 characters.');
    const stored = phase === 'challenge' ? state.initial_answer : state.recovery_answer;
    if (stored === text) return state;
    if (state.phase !== phase) throw new Error('This step is already completed. Refresh to continue.');
    const result = fixtureObservation(text);
    return write(phase === 'challenge'
      ? { ...state, phase: 'recovery', initial_answer: text, initial: result, recovery: plan.recovery }
      : { ...state, phase: 'complete', recovery_answer: text, final: result });
  },
  async report(id: string): Promise<LabReport> {
    if (!USE_FIXTURES) return apiClient(`/assessments/${id}/learning-lab`);
    const sessions: LabState[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!key?.startsWith(prefix)) continue;
      const value = read(key.slice(prefix.length));
      if (value?.assessment_id === id) sessions.push(value);
    }
    return { assessment_id: id, sessions };
  },
};
