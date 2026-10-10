import { expect, it } from 'vitest';
import { remainingSeconds, vivaAnswer } from './viva-timing';
it('uses the fixed deadline after a page reload and sends an empty timed-out answer', () => {
  expect(remainingSeconds(100000, 95000)).toBe(5);
  expect(remainingSeconds(100000, 105000)).toBe(0);
  expect(vivaAnswer('q', 'partial', 100000, 90, 2, 100000)).toMatchObject({ answer_text: '', time_taken_s: 90, tab_switches: 2, pasted: false });
  expect(vivaAnswer('q', 'my answer', 100000, 90, 0, 50000)).toMatchObject({ answer_text: 'my answer', time_taken_s: 40 });
});
