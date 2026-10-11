import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { labApi } from '../../api/learning-lab';
import { studentApi } from '../../api/student';
import { USE_FIXTURES } from '../../api/client';
import type { Assessment, LabObservation, LabState, Submission } from '../../api/types';
import { labOutcome, levelLabels } from './lab-display';
import './learning-lab.css';

export function Observation({ value }: { value: LabObservation }) {
  return <div className={`lab-observation lab-level-${value.level}`}>
    <span className="lab-pill">{levelLabels[value.level]}</span><p>{value.reasoning}</p>
    {value.suspected_gap && <p><strong>What to work on:</strong> {value.suspected_gap}</p>}
    {value.answer_quote && <details><summary>See the answer this feedback refers to</summary><blockquote>“{value.answer_quote}”</blockquote></details>}
  </div>;
}
export function LearningLabPage() {
  const { submissionId, assessmentId } = useParams();
  return <LearningLab key={submissionId || assessmentId} submissionId={submissionId} assessmentId={assessmentId} />;
}
function LearningLab({ submissionId, assessmentId }: { submissionId?: string; assessmentId?: string }) {
  const [work, setWork] = useState<{ submission: Submission; assessment: Assessment } | null>(null);
  const [state, setState] = useState<LabState | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [answer, setAnswer] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [readyForRetry, setReadyForRetry] = useState(false);
  const sending = useRef(false);
  const stepCard = useRef<HTMLElement | null>(null);
  useEffect(() => {
    let active = true;
    async function load() {
      const submission = submissionId ? await studentApi.submission(submissionId) : await studentApi.start(assessmentId || '');
      const [assessment, saved] = await Promise.all([studentApi.assessment(submission.assessment_id), labApi.get(submission.id)]);
      if (!active) return;
      setWork({ submission, assessment }); setState(saved);
      setAnswer(localStorage.getItem(`vivagrade:lab-draft:${submission.id}:${saved?.phase || 'challenge'}`) || '');
    }
    load().catch(e => { if (active) setError(e instanceof Error ? e.message : 'Practice could not open. Please try again.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [assessmentId, submissionId, attempt]);
  async function act(start: boolean) {
    if (sending.current || !work) return;
    sending.current = true; setBusy(true); setError('');
    try {
      const next = start ? await labApi.start(work.submission.id) : state && state.phase !== 'complete'
        ? await labApi.answer(work.submission.id, state.phase, answer) : state;
      if (next) {
        if (!start && state) localStorage.removeItem(`vivagrade:lab-draft:${work.submission.id}:${state.phase}`);
        setState(next); setAnswer(''); setReadyForRetry(false);
        window.requestAnimationFrame(() => stepCard.current?.scrollIntoView({ block: 'start' }));
      }
    } catch (e) { setError(e instanceof Error ? e.message : 'Your answer could not be sent. Please retry.'); }
    finally { sending.current = false; setBusy(false); }
  }
  const index = state?.phase === 'complete' ? 2 : state?.phase === 'recovery' ? 1 : 0;
  const question = state?.phase === 'recovery' ? state.recovery : state?.challenge;
  return <main className="lab-page">
    <div className="lab-topline"><Link to="/student">← My assignments</Link><span>{USE_FIXTURES || state?.mode === 'fixture' ? 'Demo mode · sample questions' : 'Practice feedback from AI'}</span></div>
    <header className="lab-heading lab-heading-simple"><p className="lab-eyebrow">STUDENT PRACTICE</p><h1>{state?.phase === 'complete' ? 'Here’s your progress.' : 'Practice what you learned.'}</h1><p>{work?.assessment.title || 'Based on your submitted assignment'}</p><p className="lab-purpose">Answer a short question, get an explanation, and try a new question. Your teacher sees where you need help.</p></header>
    <ol className="lab-steps" aria-label="Practice steps">{['Answer a question', 'Get help & try again', 'See your progress'].map((name, i) => <li key={name} className={i <= index ? 'active' : ''} aria-current={i === index ? 'step' : undefined}><span>{i + 1}</span>{name}</li>)}</ol>
    {error && <div className="lab-error" role="alert">{error}<button onClick={() => { setLoading(true); setError(''); setAttempt(n => n + 1); }}>Reload practice</button></div>}
    {loading ? <section className="lab-card" role="status">Opening your practice…</section> : !state ? <section className="lab-card" ref={stepCard}>
      {work?.submission.status === 'draft' ? <><span className="lab-kicker">START HERE</span><h2>First, submit your assignment.</h2><p>Your practice questions will be based on what you write. Finish and submit this assignment, then we’ll help you practise its ideas.</p><Link className="lab-primary" to={`/student/assessments/${work.assessment.id}`}>Write my assignment →</Link></> : <><span className="lab-kicker">YOUR ASSIGNMENT IS SAVED</span><h2>Ready to use an idea in a new situation?</h2><p>Explain your thinking in a few sentences. If you get stuck, we’ll explain the idea before you try another question.</p><div className="lab-how"><div><b>1. Answer</b><p>Try a question about an idea in your work.</p></div><div><b>2. Learn and retry</b><p>Read an explanation, then answer a new question.</p></div><div><b>3. Review</b><p>See your progress and what to work on next.</p></div></div><button className="lab-primary" disabled={busy || !work} onClick={() => void act(true)}>{busy ? 'Preparing your question…' : 'Start practice →'}</button>{busy && <p role="status">Preparing a question from your assignment. Keep this page open.</p>}<p className="lab-muted">No timer. This practice does not change your assignment grade.</p></>}
    </section> : <>
      <details className="lab-anchor"><summary>The idea from your assignment</summary><blockquote>“{state.anchor_quote}”</blockquote><span>{state.concept}</span></details>
      {state.phase === 'complete' ? <section className="lab-card" ref={stepCard}><span className="lab-kicker">PRACTICE COMPLETE</span><h2>{labOutcome(state)}</h2><p>Your teacher can see both answers and help you with the next step.</p><div className="lab-comparison"><section><h3>Your first answer</h3>{state.initial && <Observation value={state.initial} />}</section><section><h3>Your answer after the explanation</h3>{state.final && <Observation value={state.final} />}</section></div>{state.final && <div className="lab-teaching"><h3>What to do next</h3><p>{state.final.teaching}</p></div>}<Link className="lab-primary" to="/student">Back to my assignments →</Link><p className="lab-muted">This summary describes these two answers. Your teacher reviews your progress.</p></section> : state.phase === 'recovery' && !readyForRetry ? <section className="lab-card" ref={stepCard}><span className="lab-kicker">STEP 2 · GET HELP</span><h2>Read this before your next question.</h2>{state.initial && <><Observation value={state.initial} /><div className="lab-teaching"><h3>{state.initial.level === 2 ? 'Build on what you know' : 'Here’s the idea explained'}</h3><p>{state.initial.teaching}</p></div></>}<button className="lab-primary" onClick={() => { setReadyForRetry(true); window.requestAnimationFrame(() => stepCard.current?.scrollIntoView({ block: 'start' })); }}>I’m ready for the next question →</button></section> : question && <section className="lab-card" ref={stepCard}><span className="lab-kicker">{state.phase === 'challenge' ? 'STEP 1 · YOUR FIRST QUESTION' : 'STEP 2 · TRY AGAIN'}</span><h2>{state.phase === 'challenge' ? 'Read the situation. Explain your answer.' : 'Use what you just learned.'}</h2>{state.phase === 'recovery' && state.initial && <details className="lab-help"><summary>Read the explanation again</summary><p>{state.initial.teaching}</p></details>}<div className="lab-scenario">{question.scenario}</div><h3 className="lab-question">{question.question}</h3><form onSubmit={e => { e.preventDefault(); void act(false); }}><label htmlFor="lab-answer">Your answer</label><textarea id="lab-answer" required maxLength={3000} rows={5} disabled={busy} value={answer} placeholder="Tell us what you think and why. A few sentences is enough." onChange={e => { setAnswer(e.target.value); localStorage.setItem(`vivagrade:lab-draft:${work?.submission.id}:${state.phase}`, e.target.value); }} /><div className="lab-answer-footer"><span>{answer.length}/3,000 · Take your time.</span><button className="lab-primary" disabled={busy || !answer.trim()}>{busy ? 'Preparing your feedback…' : state.phase === 'challenge' ? 'Get feedback →' : 'See my progress →'}</button></div>{busy && <p role="status">Your answer is being reviewed. It stays here if sending fails.</p>}</form></section>}
    </>}
  </main>;
}
