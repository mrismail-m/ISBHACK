import type { LabState } from '../../api/types';

export const levelLabels = ['Not yet demonstrated', 'Partially demonstrated', 'Demonstrated'];
export function labOutcome(state: LabState): string {
  if (!state.final || !state.initial) return 'In progress';
  if (state.final.level < 2) return state.final.level > state.initial.level ? 'Progress · follow-up needed' : 'Follow-up needed';
  return state.final.level > state.initial.level ? 'Applied after explanation' : 'Applied in both scenarios';
}
