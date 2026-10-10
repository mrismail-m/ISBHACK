import { useEffect, useMemo, useRef, useState } from 'react';
import { activityApi } from '../../api/activity';
import type { ActivityEvents, ActivitySummary, PasteChunk } from '../../api/types';
import { buildTimeline, createReplay, segments, type ReplayState } from '../../lib/replay-core';
import './insights.css';

export function TypedPastedBar({ summary }: { summary: ActivitySummary }) {
  return <div className="typed-pasted"><p>Typed or restored <strong>{summary.typed_pct.toFixed(1)}%</strong> · Pasted <strong>{summary.pasted_pct.toFixed(1)}%</strong></p><div className="authorship-bar" aria-label={`${summary.typed_pct}% typed or restored, ${summary.pasted_pct}% pasted`}><span style={{ width: `${summary.typed_pct}%` }} /><span className="pasted" style={{ width: `${summary.pasted_pct}%` }} /></div><p className="insight-muted">Writing signals support teacher review. They do not apply a mark penalty.</p></div>;
}
export function PasteChunkList({ chunks, onJump }: { chunks: PasteChunk[]; onJump?: (chunk: PasteChunk) => void }) {
  return <section><h3>Pasted text</h3>{chunks.length ? <ol className="paste-chunks">{chunks.map(c => <li key={`${c.session_id}:${c.event_seq}`}><div><strong>{c.chars} characters</strong> · {c.survived_pct.toFixed(1)}% kept{c.major && <span className="chunk-label">Large paste</span>}<p className="insight-muted">{new Date(c.at).toLocaleString()} · {c.survived_chars} characters still present</p></div>{onJump && <button onClick={() => onJump(c)}>Jump to paste</button>}</li>)}</ol> : <p>No external paste chunks of 40 characters or more.</p>}</section>;
}
export function AuthorshipMap({ state }: { state: ReplayState }) {
  return <section><h3>Writing map</h3><p className="insight-muted">Underlined text is pasted. Plain text is typed or restored by undo/redo.</p><pre className="authorship-document">{segments(state).map(s => s.tag === 'P' ? <mark className="paste-highlight" key={s.start}>{state.doc.slice(s.start, s.end)}</mark> : <span key={s.start}>{state.doc.slice(s.start, s.end)}</span>)}</pre></section>;
}
export function ActivityHeatmap({ summary }: { summary: ActivitySummary }) {
  return <section><h3>Writing activity</h3><p>{summary.active_minutes} active minutes · {summary.span_minutes} minutes elapsed · {summary.tab_switches} tab switches</p>{summary.heatmap.length ? <div className="activity-buckets">{summary.heatmap.map(b => <div key={b.bucket_start} className="activity-bucket"><time>{new Date(b.bucket_start).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}</time><meter min={0} max={Math.max(1, ...summary.heatmap.map(row => row.edits))} value={b.edits} aria-label={`${b.bucket_start}: ${b.edits} edits`} /><span>{b.edits} edits</span><small>{b.typed_chars} typed, {b.pasted_chars} pasted</small></div>)}</div> : <p>No editing activity recorded.</p>}</section>;
}
export function ReplayViewer({ activity, selectedPaste }: { activity: ActivityEvents; selectedPaste?: PasteChunk | null }) {
  const replay = useMemo(() => createReplay(activity), [activity]);
  const [index, setIndex] = useState(0);
  const position = useRef(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [skipIdle, setSkipIdle] = useState(true);
  const timeline = useMemo(() => buildTimeline(activity, { maxIdleMs: skipIdle ? 5000 : Infinity }), [activity, skipIdle]);
  const move = (next: number) => { position.current = next; setIndex(next); };
  useEffect(() => {
    if (!selectedPaste) return;
    const target = replay.events.findIndex(e => e.session_id === selectedPaste.session_id && e.seq === selectedPaste.event_seq);
    if (target >= 0) {
      position.current = target + 1;
      // This synchronizes the replay with a paste selected outside this component.
      // oxlint-disable-next-line react/set-state-in-effect
      setIndex(target + 1);
      // oxlint-disable-next-line react/set-state-in-effect
      setPlaying(false);
    }
  }, [selectedPaste, replay]);
  useEffect(() => {
    if (!playing) return;
    let elapsed = timeline[position.current - 1]?.time || 0;
    let previous = performance.now();
    const timer = window.setInterval(() => {
      const now = performance.now(); elapsed += (now - previous) * speed; previous = now;
      const next = timeline.findLastIndex(e => e.time <= elapsed) + 1;
      position.current = next; setIndex(next);
      if (next === replay.events.length) setPlaying(false);
    }, 40);
    return () => window.clearInterval(timer);
  }, [playing, speed, timeline, replay.events.length]);
  const state = replay.at(index);
  return <section className="replay-viewer"><h3>Writing replay</h3><p className="insight-muted">Reconstructed from editor events. This is not a screen recording.</p>
    <div className="replay-controls"><button disabled={!replay.events.length} onClick={() => { if (index === replay.events.length) move(0); setPlaying(p => !p); }}>{playing ? 'Pause' : 'Play'}</button><label>Speed <select value={speed} onChange={e => setSpeed(Number(e.target.value))}>{[1, 2, 4, 8].map(s => <option key={s} value={s}>{s}x</option>)}</select></label><label><input type="checkbox" checked={skipIdle} onChange={e => setSkipIdle(e.target.checked)} /> Skip idle time</label><button onClick={() => { const next = replay.events.findIndex((e, i) => i >= index && (e.k === 'paste' || e.k === 'drop')); if (next >= 0) { setPlaying(false); move(next + 1); } }} disabled={!replay.events.some((e, i) => i >= index && (e.k === 'paste' || e.k === 'drop'))}>Next paste</button></div>
    <label className="replay-scrubber">Event {index} of {replay.events.length}<input aria-label="Replay position" type="range" min={0} max={replay.events.length} value={index} onChange={e => { setPlaying(false); move(Number(e.target.value)); }} /></label>
    <p className="insight-muted">{index ? `Session ${replay.events[index - 1].session_id.slice(0, 8)} · ${replay.events[index - 1].k}` : 'Before writing began'}</p><AuthorshipMap state={state} />
  </section>;
}
// Ismail can embed this directly in review detail, or pass existing activity/summary to InsightsView.
export function InsightsView({ activity, summary }: { activity: ActivityEvents; summary: ActivitySummary }) {
  const [paste, setPaste] = useState<PasteChunk | null>(null);
  return <div className="activity-insights"><TypedPastedBar summary={summary} /><PasteChunkList chunks={summary.paste_chunks} onJump={setPaste} /><ReplayViewer activity={activity} selectedPaste={paste} /><ActivityHeatmap summary={summary} /></div>;
}
export function ActivityInsights({ submissionId }: { submissionId: string }) {
  return <ActivityInsightsLoader key={submissionId} submissionId={submissionId} />;
}
function ActivityInsightsLoader({ submissionId }: { submissionId: string }) {
  const [data, setData] = useState<{ activity: ActivityEvents; summary: ActivitySummary } | null>(null);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    Promise.all([activityApi.events(submissionId), activityApi.summary(submissionId)]).then(([activity, summary]) => { if (active) setData({ activity, summary }); }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [submissionId, attempt]);
  if (error) return <section role="alert">Writing record could not load: {error} <button onClick={() => { setError(''); setAttempt(a => a + 1); }}>Retry</button></section>;
  if (!data) return <p role="status">Loading writing record...</p>;
  if (!data.activity.events.length) return <p>No writing record for this work.</p>;
  return <InsightsView {...data} />;
}
