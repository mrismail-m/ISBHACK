import type { LabState } from '../../api/types';

export const levelLabels = ['Needs more explanation', 'Partly explained', 'Explained correctly'];
export function labOutcome(state: LabState): string {
  if (!state.final || !state.initial) return 'In progress';
  if (state.final.level < 2) return state.final.level > state.initial.level ? 'Improved, keep practising' : 'Needs more practice';
  return state.final.level > state.initial.level ? 'Your explanation improved' : 'You explained both answers clearly';
}
