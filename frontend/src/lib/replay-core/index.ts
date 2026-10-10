import type { ActivityEvent, ActivityEvents, ActivitySummary, PasteChunk } from '../../api/types';
export interface AuthorshipSegment { start: number; end: number; tag: 'T' | 'P' | 'U'; src: string | null }
interface Unit { tag: AuthorshipSegment['tag']; src: string | null }
export interface ReplayState { doc: string; units: Unit[]; cuts: Record<string, string> }
export type SessionEvent = ActivityEvent & { session_id: string };
const nonEdit = new Set(['start', 'end', 'blur', 'focus', 'hidden', 'visible']);
export const emptyState = (): ReplayState => ({ doc: '', units: [], cuts: {} });
export function orderedEvents(activity: ActivityEvents): SessionEvent[] {
  const starts = new Map(activity.sessions.map(s => [s.session_id, Date.parse(s.started_at)]));
  return [...activity.events].sort((a, b) => (starts.get(a.session_id)! - starts.get(b.session_id)!) || a.session_id.localeCompare(b.session_id) || a.seq - b.seq);
}
function internalPaste(state: ReplayState, event: SessionEvent) {
  const trimmed = event.text.trim();
  return event.k === 'paste' && trimmed.length >= 20 && (state.doc.includes(trimmed) || state.cuts[event.session_id] === trimmed);
}
export function applyEvent(state: ReplayState, event: SessionEvent): ReplayState {
  if (nonEdit.has(event.k)) return state;
  if (event.from < 0 || event.to < event.from || event.to > state.doc.length) throw new Error(`Invalid UTF-16 range at ${event.session_id}:${event.seq}`);
  const pasted = (event.k === 'paste' || event.k === 'drop') && !internalPaste(state, event);
  const tag = pasted ? 'P' : (event.k === 'undo' || event.k === 'redo') ? 'U' : 'T';
  const src = pasted ? `${event.session_id}:${event.seq}` : null;
  const cuts = event.k === 'cut' ? { ...state.cuts, [event.session_id]: state.doc.slice(event.from, event.to).trim() } : state.cuts;
  return { doc: state.doc.slice(0, event.from) + event.text + state.doc.slice(event.to),
    units: [...state.units.slice(0, event.from), ...Array.from({ length: event.text.length }, () => ({ tag, src } as Unit)), ...state.units.slice(event.to)], cuts };
}
export function segments(state: ReplayState): AuthorshipSegment[] {
  const result: AuthorshipSegment[] = [];
  state.units.forEach((unit, i) => {
    const previous = result.at(-1);
    if (previous && previous.tag === unit.tag && previous.src === unit.src) previous.end++;
    else result.push({ start: i, end: i + 1, ...unit });
  });
  return result;
}
export function createReplay(activity: ActivityEvents) {
  const events = orderedEvents(activity);
  const checkpoints = new Map<number, ReplayState>([[0, emptyState()]]);
  let state = emptyState();
  events.forEach((event, i) => { state = applyEvent(state, event); if ((i + 1) % 200 === 0) checkpoints.set(i + 1, state); });
  return { events, at(index: number): ReplayState {
    const count = Math.max(0, Math.min(events.length, Math.floor(index)));
    const checkpoint = Math.floor(count / 200) * 200;
    let current = checkpoints.get(checkpoint)!;
    for (let i = checkpoint; i < count; i++) current = applyEvent(current, events[i]);
    return current;
  } };
}
export const docAt = (events: ActivityEvents, index: number) => createReplay(events).at(index).doc;
export const authorshipAt = (events: ActivityEvents, index: number) => segments(createReplay(events).at(index));
export function buildTimeline(activity: ActivityEvents, { maxIdleMs = 5000 } = {}) {
  let elapsed = 0;
  const events = orderedEvents(activity);
  return events.map((event, i) => {
    const previous = events[i - 1];
    const newSession = previous && previous.session_id !== event.session_id;
    elapsed += !previous ? 0 : newSession ? 1000 : Math.min(maxIdleMs, Math.max(0, event.t - previous.t));
    return { index: i + 1, time: elapsed, session_id: event.session_id, new_session: Boolean(newSession), paste: event.k === 'paste' || event.k === 'drop' };
  });
}
export function summarizeActivity(submission_id: string, activity: ActivityEvents, pasteFlagChars = 500, bucket: 'auto' | 'minute' | 'hour' = 'auto'): ActivitySummary {
  const starts = new Map(activity.sessions.map(s => [s.session_id, Date.parse(s.started_at)]));
  const events = orderedEvents(activity);
  let state = emptyState();
  let inserted = 0, deleted = 0;
  const chunks: PasteChunk[] = [];
  const edits: { at: number; typed: number; pasted: number }[] = [];
  const times = events.map(e => starts.get(e.session_id)! + e.t);
  for (const event of events) {
    if (nonEdit.has(event.k)) continue;
    const at = starts.get(event.session_id)! + event.t;
    const pasted = (event.k === 'paste' || event.k === 'drop') && !internalPaste(state, event);
    inserted += event.text.length; deleted += event.to - event.from;
    edits.push({ at, typed: pasted ? 0 : event.text.length, pasted: pasted ? event.text.length : 0 });
    if (pasted && event.text.length >= 40) chunks.push({ session_id: event.session_id, event_seq: event.seq, at: new Date(at).toISOString().replace('.000Z', 'Z'), t: event.t, chars: event.text.length, survived_chars: 0, survived_pct: 0, major: event.text.length >= pasteFlagChars, declared_source: null });
    state = applyEvent(state, event);
  }
  const round = (n: number, places = 1) => Math.round(n * 10 ** places) / 10 ** places;
  for (const chunk of chunks) {
    chunk.survived_chars = state.units.filter(u => u.src === `${chunk.session_id}:${chunk.event_seq}`).length;
    chunk.survived_pct = round(chunk.survived_chars / chunk.chars * 100);
  }
  const span = times.length ? (Math.max(...times) - Math.min(...times)) / 60000 : 0;
  const selected = bucket === 'auto' ? span > 180 ? 'hour' : 'minute' : bucket;
  const buckets = new Map<number, ActivitySummary['heatmap'][number]>();
  for (const edit of edits) {
    const size = selected === 'hour' ? 3600000 : 60000;
    const start = Math.floor(edit.at / size) * size;
    const row = buckets.get(start) || { bucket_start: new Date(start).toISOString().replace('.000Z', 'Z'), edits: 0, typed_chars: 0, pasted_chars: 0 };
    row.edits++; row.typed_chars += edit.typed; row.pasted_chars += edit.pasted; buckets.set(start, row);
  }
  const pastedPct = state.doc.length ? round(state.units.filter(u => u.tag === 'P').length / state.doc.length * 100) : 0;
  return { submission_id, final_chars: state.doc.length, typed_pct: state.doc.length ? round(100 - pastedPct) : 0, pasted_pct: pastedPct,
    paste_chunks: chunks, revision_ratio: inserted ? round(deleted / inserted, 3) : 0, active_minutes: new Set(edits.map(e => Math.floor(e.at / 60000))).size,
    span_minutes: round(span), tab_switches: events.filter(e => e.k === 'hidden').length, sessions: activity.sessions.length, bucket: selected,
    heatmap: [...buckets.entries()].sort((a, b) => a[0] - b[0]).map(([, row]) => row) };
}
export const heatmap = (events: ActivityEvents, bucket: 'minute' | 'hour') => summarizeActivity('', events, 500, bucket).heatmap;
