import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { FeedbackView, ResultView } from './StudentResult';
import type { Feedback, StudentResult } from '../../api/types';

const feedback: Feedback = { mode: 'hints', strengths: [], improvements: [{ criterion_id: 'c1', text: 'Review complexity.', quote: 'fast', hint: 'What is the worst case?', explanation: 'An explanation that should be hidden in hints mode.' }], next_step: 'Rewrite.', topics: [] };
describe('released result display', () => {
  it('never renders the full explanation when feedback mode is hints', () => {
    const html = renderToStaticMarkup(<FeedbackView feedback={feedback} />);
    expect(html).toContain('What is the worst case?');
    expect(html).not.toContain('An explanation that should be hidden');
  });
  it('uses the server total including grace without recomputing grade math', () => {
    const result: StudentResult = { submission_id: 's', assessment_id: 'a', max_marks: 20, work_marks: 15.5, understanding: null, viva_weight: 0.3, final_marks: 15.2, grace_marks: 2, final_with_grace: 17.2, final_pct: 86, released_at: '2026-10-10T09:00:00Z', feedback };
    const html = renderToStaticMarkup(<ResultView result={result} />);
    expect(html).toContain('17.2');
    expect(html).toContain('Includes +2.0 grace marks');
    expect(html).toContain('Viva not taken');
  });
});
