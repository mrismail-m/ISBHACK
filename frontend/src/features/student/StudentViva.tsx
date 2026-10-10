import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { studentApi } from '../../api/student';
import { USE_FIXTURES } from '../../api/client';
import type { Assessment, VivaAnswer, VivaStart } from '../../api/types';
import { remainingSeconds, vivaAnswer } from './viva-timing';
interface Progress { viva: VivaStart; index: number; deadline: number; answer: string; switches: number; pending: VivaAnswer | null; done: boolean }
export function StudentVivaPage() {
  const { submissionId = '' } = useParams();
  return <VivaSession key={submissionId} submissionId={submissionId} />;
}
function VivaSession({ submissionId }: { submissionId: string }) {
  const key = `vivagrade:viva:${localStorage.getItem('currentUserId')}:${submissionId}`;
  const [progress, setProgress] = useState<Progress | null>(() => {
    try { return JSON.parse(localStorage.getItem(key) || 'null') as Progress | null; } catch { return null; }
  });
  const current = useRef(progress);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const sending = useRef(false);
  const [remaining, setRemaining] = useState(progress ? remainingSeconds(progress.deadline) : 0);
  const [notice, setNotice] = useState('');
  const update = useCallback((next: Progress) => { current.current = next; localStorage.setItem(key, JSON.stringify(next)); setProgress(next); }, [key]);
  useEffect(() => {
    let active = true;
    studentApi.submission(submissionId).then(s => studentApi.assessment(s.assessment_id)).then(a => { if (active) setAssessment(a); }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [submissionId]);
  const finish = useCallback(async (state: Progress) => {
    await studentApi.finishViva(submissionId);
    update({ ...state, done: true, pending: null });
  }, [submissionId, update]);
  const submit = useCallback(async () => {
    const state = current.current;
    if (!state || state.done || sending.current) return;
    sending.current = true; setBusy(true); setError('');
    try {
      if (state.index >= state.viva.questions.length) { await finish(state); return; }
      const question = state.viva.questions[state.index];
      const answer = state.pending || vivaAnswer(question.id, state.answer, state.deadline, question.time_limit_s, state.switches);
      const pending = { ...state, pending: answer }; update(pending);
      await studentApi.answerViva(submissionId, answer);
      const index = state.index + 1;
      const next: Progress = { ...pending, index, pending: null, answer: '', switches: 0, deadline: Date.now() + (state.viva.questions[index]?.time_limit_s || 0) * 1000 };
      update(next); setNotice('');
      if (index >= state.viva.questions.length) await finish(next);
    } catch (e) { setError(e instanceof Error ? e.message : 'Answer could not be sent.'); }
    finally { sending.current = false; setBusy(false); }
  }, [finish, submissionId, update]);
  useEffect(() => {
    if (!progress || progress.done || progress.pending || progress.index >= progress.viva.questions.length) return;
    const tick = () => { const left = remainingSeconds(progress.deadline); setRemaining(left); if (!left) void submit(); };
    tick(); const interval = window.setInterval(tick, 250);
    return () => window.clearInterval(interval);
  }, [progress, submit]);
  useEffect(() => {
    const hidden = () => { const state = current.current; if (document.hidden && state && !state.done && !state.pending) update({ ...state, switches: state.switches + 1 }); };
    document.addEventListener('visibilitychange', hidden);
    return () => document.removeEventListener('visibilitychange', hidden);
  }, [update]);
  async function start() {
    setBusy(true); setError('');
    try {
      const viva = await studentApi.startViva(submissionId);
      if (!viva.questions.length) throw new Error('No viva questions were returned. Tell your teacher.');
      update({ viva, index: 0, deadline: Date.now() + viva.questions[0].time_limit_s * 1000, answer: '', switches: 0, pending: null, done: false });
    } catch (e) { setError(e instanceof Error ? e.message : 'Questions could not be prepared.'); }
    finally { setBusy(false); }
  }
  const question = progress?.viva.questions[progress.index];
  return <main className="student-page viva-page">{USE_FIXTURES && <p className="demo-note">Demo viva. Questions and completion are simulated locally.</p>}
    {error && <div role="alert" className="error">{error} Your written submission is saved.{progress && <button disabled={busy} onClick={() => void submit()}>Retry sending</button>}</div>}
    {!progress ? <><h1>Explain your thinking.</h1>{assessment ? <><p>{assessment.viva_question_count} questions, {assessment.viva_time_limit_s} seconds each.</p><ul><li>Questions are about your own submitted work.</li><li>Paste and drag-and-drop are blocked in answer boxes.</li><li>Leaving this tab is counted and shown to your teacher.</li><li>A timed-out answer receives no credit. Your teacher reviews the outcome.</li></ul><p>Your timer starts after you choose Start viva.</p><button className="primary" disabled={busy || !assessment.viva_enabled} onClick={() => void start()}>{busy ? 'Preparing your questions...' : 'Start viva'}</button></> : !error && <p role="status">Loading viva settings...</p>}<p><Link to="/student">Back to my work</Link></p></> : progress.done ? <><h1>Viva complete.</h1><p>Your teacher can now review your work and answers.</p><Link className="primary" to={`/student/submissions/${submissionId}/result`}>Check released feedback</Link></> : question ? <>
      <p>Question {progress.index + 1} of {progress.viva.questions.length}</p><div className="viva-timer"><label>Time left <strong>{Math.floor(remaining / 60)}:{String(remaining % 60).padStart(2, '0')}</strong><progress max={question.time_limit_s} value={remaining} /></label><span className="sr-only" aria-live="polite">{remaining === 30 || remaining === 10 ? `${remaining} seconds left` : ''}</span></div><h1>{question.text}</h1>
      <label>Your answer<textarea rows={7} value={progress.answer} disabled={busy || Boolean(progress.pending)} onChange={e => update({ ...progress, answer: e.target.value })} onPaste={e => { e.preventDefault(); setNotice('Paste is off in viva answers. Please write in your own words.'); }} onDrop={e => { e.preventDefault(); setNotice('Drag-and-drop is off in viva answers.'); }} /></label><p role="status">{notice}</p><p className="muted">Paste is off here. Tab switches recorded: {progress.switches}.</p><button className="primary" disabled={busy} onClick={() => void submit()}>{busy ? 'Sending your answer...' : progress.pending ? 'Retry sending answer' : 'Submit answer'}</button>
    </> : <><p role="status">{busy ? 'Completing your viva...' : 'Your answers were sent. Complete the viva to finish.'}</p><button className="primary" disabled={busy} onClick={() => void submit()}>Complete viva</button></>}
    <p className="muted">Recorded: answers, time taken and tab switches. No screen, webcam or typing outside these answer boxes.</p>
  </main>;
}
