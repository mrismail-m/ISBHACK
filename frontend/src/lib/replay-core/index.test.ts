import { describe, expect, it } from 'vitest';
import cases from '../../../../fixtures/activity/cases.json';
import { createReplay, summarizeActivity } from './index';
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
