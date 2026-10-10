import type { VivaAnswer } from '../../api/types';
export function remainingSeconds(deadline: number, now = Date.now()): number {
  return Math.max(0, Math.ceil((deadline - now) / 1000));
}
export function vivaAnswer(question_id: string, answer: string, deadline: number, limit: number, tab_switches: number, now = Date.now()): VivaAnswer {
  const elapsed = Math.max(0, (now - (deadline - limit * 1000)) / 1000);
  return { question_id, answer_text: elapsed >= limit ? '' : answer, time_taken_s: Math.min(limit, elapsed), pasted: false, tab_switches };
}
