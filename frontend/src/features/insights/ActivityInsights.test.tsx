import { expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import cases from '../../../../fixtures/activity/cases.json';
import type { ActivityEvents } from '../../api/types';
import { createReplay, summarizeActivity } from '../../lib/replay-core';
import { AuthorshipMap, PasteChunkList, TypedPastedBar } from './ActivityInsights';
it('highlights only surviving pasted text and shows the server summary as a signal', () => {
  const fixture = cases.find(c => c.name === 'paste_heavy_edit')!;
  const activity = fixture.activity as ActivityEvents;
  const state = createReplay(activity).at(activity.events.length);
  const summary = summarizeActivity('s', activity, 60);
  const html = renderToStaticMarkup(<><AuthorshipMap state={state} /><TypedPastedBar summary={summary} /><PasteChunkList chunks={summary.paste_chunks} /></>);
  expect(html).toContain('66.7%');
  expect(html).toContain('25.0%');
  expect(html).toContain('do not apply a mark penalty');
  expect(html).toContain('paste-highlight');
  expect(html).toContain('abcdefghij');
});
