import { expect, it } from 'vitest';
import type { LabObservation, LabState } from '../../api/types';
import { labOutcome } from './lab-display';

const observation = (level: 0 | 1 | 2): LabObservation => ({ level, reasoning: '', suspected_gap: '', answer_quote: '', teaching: '' });
const state = (initial: 0 | 1 | 2, final: 0 | 1 | 2 | null): LabState => ({
  id: 'lab', submission_id: 's', assessment_id: 'a', concept: '', anchor_quote: '',
  phase: final === null ? 'recovery' : 'complete', challenge: { scenario: '', question: '' },
  recovery: null, initial_answer: '', recovery_answer: '', initial: observation(initial),
  final: final === null ? null : observation(final), mode: 'fixture', created_at: '',
});
it('does not call partial improvement a completed learning outcome', () => {
  expect(labOutcome(state(0, 1))).toBe('Progress · follow-up needed');
  expect(labOutcome(state(0, 2))).toBe('Applied after explanation');
});
it('reports regression, unchanged responses, and unfinished practice honestly', () => {
  expect(labOutcome(state(2, 0))).toBe('Follow-up needed');
  expect(labOutcome(state(1, 1))).toBe('Follow-up needed');
  expect(labOutcome(state(2, 2))).toBe('Applied in both scenarios');
  expect(labOutcome(state(0, null))).toBe('In progress');
});
