import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { labApi } from '../../api/learning-lab';
import { studentApi } from '../../api/student';
import { USE_FIXTURES } from '../../api/client';
import type { LabObservation, LabState } from '../../api/types';
import './learning-lab.css';
import { labOutcome, levelLabels } from './lab-display';

export function Observation({ value }: { value: LabObservation }) {
  return <div className={`lab-observation lab-level-${value.level}`}>
    <span className="lab-pill">{levelLabels[value.level]}</span>
    <p>{value.reasoning}</p>
    {value.answer_quote && <blockquote>“{value.answer_quote}”</blockquote>}
    {value.suspected_gap && <p><strong>Possible gap:</strong> {value.suspected_gap}</p>}
  </div>;
}
export function LearningLabPage() {
  const { submissionId, assessmentId } = useParams();
  return <LearningLab key={submissionId || assessmentId} submissionId={submissionId} assessmentId={assessmentId} />;
}
function LearningLab({ submissionId, assessmentId }: { submissionId?: string; assessmentId?: string }) {
  const [id, setId] = useState(submissionId || '');
  const [state, setState] = useState<LabState | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [answer, setAnswer] = useState('');
  const [attempt, setAttempt] = useState(0);
  const sending = useRef(false);
  useEffect(() => {
    let active = true;
    async function load() {
      const actual = submissionId || (await studentApi.start(assessmentId || '')).id;
      const saved = await labApi.get(actual);
      if (!active) return;
      setId(actual); setState(saved);
      setAnswer(localStorage.getItem(`vivagrade:lab-draft:${actual}:${saved?.phase || 'challenge'}`) || '');
    }
    load().catch(e => { if (active) setError(e instanceof Error ? e.message : 'Could not open the lab.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [assessmentId, submissionId, attempt]);
  async function act(start: boolean) {
    if (sending.current) return;
    sending.current = true; setBusy(true); setError('');
    try {
      const next = start ? await labApi.start(id) : state && state.phase !== 'complete'
        ? await labApi.answer(id, state.phase, answer) : state;
      if (next) {
        if (!start && state) localStorage.removeItem(`vivagrade:lab-draft:${id}:${state.phase}`);
        setState(next); setAnswer('');
      }
    } catch (e) { setError(e instanceof Error ? e.message : 'Could not save your answer. Please retry.'); }
    finally { sending.current = false; setBusy(false); }
  }
  const index = state?.phase === 'complete' ? 3 : state?.phase === 'recovery' ? 2 : 0;
  const question = state?.phase === 'recovery' ? state.recovery : state?.challenge;
  return <main className="lab-page">
    <div className="lab-topline"><Link to="/student">← My classroom</Link><span>{USE_FIXTURES || state?.mode === 'fixture' ? 'Offline fixture · limited demo rubric' : 'Formative practice · AI observations'}</span></div>
    <header className="lab-heading"><p className="lab-eyebrow">LEARNING LAB</p><h1>Don’t just explain it.<br /><em>Put it to the test.</em></h1><p>Try a changed situation. Learn from your reasoning. Apply it somewhere new.</p></header>
    <ol className="lab-steps" aria-label="Learning progress">{['Apply', 'Learn', 'Try again', 'Reflect'].map((name, i) => <li key={name} className={i <= index ? 'active' : ''} aria-current={i === index ? 'step' : undefined}><span>{i + 1}</span>{name}</li>)}</ol>
    {error && <div className="lab-error" role="alert">{error} {loading === false && !id && <button onClick={() => { setLoading(true); setError(''); setAttempt(n => n + 1); }}>Retry opening</button>}</div>}
    {loading ? <section className="lab-card" role="status">Opening your learning session…</section> : !state ? <section className="lab-card lab-intro"><div><span className="lab-kicker">ONE IDEA. TWO DIFFERENT SITUATIONS.</span><h2>What happens when the conditions change?</h2><p>We’ll take one idea from your submitted assignment and change the situation. Your first answer shapes a short explanation. Then you’ll try a new scenario.</p><p className="lab-muted">Your teacher can review both answers. This practice does not change your assignment grade.</p><button className="lab-primary" disabled={busy || !id} onClick={() => void act(true)}>{busy ? 'Designing your experiment…' : 'Start my learning experiment →'}</button>{busy && <p role="status">Preparing two scenarios from your assignment. This can take up to a minute.</p>}</div><div className="lab-illustration" aria-hidden="true"><span>01</span><div>YOUR IDEA</div><b>↓ change one condition</b><div>NEW SITUATION</div><b>↓ explain → apply again</b><div className="lab-illustration-end">VISIBLE LEARNING</div></div></section> : <>
      <section className="lab-anchor"><span className="lab-kicker">FROM YOUR ASSIGNMENT</span><blockquote>“{state.anchor_quote}”</blockquote><span>{state.concept}</span></section>
      {state.phase === 'complete' ? <>
        <section className="lab-card"><p className="lab-kicker">YOUR LEARNING EVIDENCE</p><h2>{labOutcome(state)}</h2><p>These are observations from two attempts, ready for your teacher to review.</p><div className="lab-comparison"><section><h3>Before the explanation</h3>{state.initial && <Observation value={state.initial} />}</section><section><h3>In the new scenario</h3>{state.final && <Observation value={state.final} />}</section></div>{state.final && <div className="lab-teaching"><h3>Keep exploring</h3><p>{state.final.teaching}</p></div>}<p className="lab-muted">Two answers offer limited evidence, not proof of lasting mastery. Your teacher decides what comes next.</p><Link className="lab-primary" to="/student">Back to my classroom →</Link></section>
      </> : <>
        {state.initial && <section className="lab-card"><span className="lab-kicker">A SHORT EXPLANATION FOR YOUR NEXT ATTEMPT</span><h2>Let’s examine the mechanism.</h2><Observation value={state.initial} /><div className="lab-teaching"><h3>{state.initial.level === 2 ? 'Extend the idea' : 'Try this way of thinking'}</h3><p>{state.initial.teaching}</p></div></section>}
        {question && <section className="lab-card"><span className="lab-kicker">{state.phase === 'challenge' ? 'EXPERIMENT 01 · CHANGE THE CONDITIONS' : 'EXPERIMENT 02 · A DIFFERENT SITUATION'}</span><h2>{state.phase === 'challenge' ? 'Does your idea still hold?' : 'Now, take the idea further.'}</h2><div className="lab-scenario">{question.scenario}</div><h3 className="lab-question">{question.question}</h3><form onSubmit={e => { e.preventDefault(); void act(false); }}><label htmlFor="lab-answer">Explain your reasoning</label><textarea id="lab-answer" required maxLength={3000} rows={5} disabled={busy} value={answer} placeholder="What changes, and why? Walk through the reasoning." onChange={e => { setAnswer(e.target.value); localStorage.setItem(`vivagrade:lab-draft:${id}:${state.phase}`, e.target.value); }} /><div className="lab-answer-footer"><span>{answer.length}/3,000 · No timer. Think it through.</span><button className="lab-primary" disabled={busy || !answer.trim()}>{busy ? 'Examining your reasoning…' : state.phase === 'challenge' ? 'Explore my reasoning →' : 'See my learning evidence →'}</button></div>{busy && <p role="status">Checking the reasoning and preparing feedback. Your answer stays here if the request fails.</p>}</form></section>}
      </>}
    </>}
  </main>;
}
