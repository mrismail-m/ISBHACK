import { describe, expect, it } from 'vitest';
import cases from '../../../../fixtures/activity/cases.json';
import demos from '../../../../fixtures/activity/demo_sessions.json';
import { buildTimeline, createReplay, summarizeActivity } from './index';
import type { ActivityEvents } from '../../api/types';
describe('shared activity fixtures', () => {
  for (const fixture of cases) it(fixture.name, () => {
    const activity = fixture.activity as ActivityEvents;
    expect(createReplay(activity).at(activity.events.length).doc).toBe(fixture.expected.doc);
    const summary = summarizeActivity(fixture.submission_id, activity, fixture.paste_flag_chars);
    const { doc: _doc, paste_chunks, ...expected } = fixture.expected;
    expect(summary).toMatchObject(expected);
    expect(summary.paste_chunks).toHaveLength(paste_chunks.length);
    paste_chunks.forEach((chunk, i) => expect(summary.paste_chunks[i]).toMatchObject(chunk));
  });
});
describe('recorded real editor demos', () => {
  for (const fixture of demos.sessions) it(fixture.name, () => {
    const activity = fixture.activity as ActivityEvents;
    expect(createReplay(activity).at(activity.events.length).doc).toBe(fixture.expected.doc);
    const summary = summarizeActivity(fixture.submission_id, activity, fixture.paste_flag_chars);
    const normalize = (value: typeof summary) => ({ ...value, paste_chunks: value.paste_chunks.map(c => ({ ...c, at: new Date(c.at).toISOString() })) });
    expect(normalize(summary)).toEqual(normalize(fixture.expected.summary as typeof summary));
    expect(summary.pasted_pct).toBe(fixture.name === 'pasted' ? 100 : 0);
    expect(summary.paste_chunks.some(c => c.major)).toBe(fixture.name === 'pasted');
  });
});
it('seeks backwards and forwards across replay checkpoints', () => {
  const activity: ActivityEvents = { sessions: [{ session_id: 'long', started_at: '2026-10-10T08:00:00Z' }], events: Array.from({ length: 450 }, (_, seq) => ({ session_id: 'long', seq, t: seq * 10, k: 'type', from: seq, to: seq, text: 'x' })) };
  const replay = createReplay(activity);
  for (const index of [450, 199, 400, 0, 201, 200]) expect(replay.at(index).doc).toBe('x'.repeat(index));
});
it('compresses idle gaps and keeps session boundaries visible', () => {
  const activity: ActivityEvents = { sessions: [{ session_id: 'one', started_at: '2026-10-10T08:00:00Z' }, { session_id: 'two', started_at: '2026-10-10T09:00:00Z' }], events: [{ session_id: 'one', seq: 0, t: 0, k: 'start', from: 0, to: 0, text: '' }, { session_id: 'one', seq: 1, t: 60000, k: 'focus', from: 0, to: 0, text: '' }, { session_id: 'two', seq: 0, t: 0, k: 'start', from: 0, to: 0, text: '' }] };
  expect(buildTimeline(activity).map(e => e.time)).toEqual([0, 5000, 6000]);
  expect(buildTimeline(activity)[2].new_session).toBe(true);
  expect(buildTimeline(activity, { maxIdleMs: Infinity })[1].time).toBe(60000);
});

