import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { studentApi } from '../../api/student';
import type { Assessment, Submission } from '../../api/types';
import { ActivityRecorder } from './activity-recorder';
const MarkdownEditor = lazy(() => import('./MarkdownEditor').then(m => ({ default: m.MarkdownEditor })));
import './student.css';
export function AssessmentList() {
  const [assessments, setAssessments] = useState<Assessment[] | null>(null);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    studentApi.assessments().then(data => { if (active) setAssessments(data.filter(a => a.status === 'open')); }).catch(e => { if (active) setError(String(e.message)); });
    return () => { active = false; };
  }, [attempt]);
  return <main className="student-page">
    <p className="eyebrow">YOUR CLASSROOM</p><h1>A little work.<br />A deeper understanding.</h1>
    <p className="lead">Write your answer, explain your thinking, and learn from your feedback.</p>
    
    {error ? <div role="alert" className="error">{error} <button onClick={() => { setError(''); setAttempt(a => a + 1); }}>Try again</button></div> : !assessments ? <p role="status">Loading your assessments...</p> : !assessments.length ? <p>No open assessments yet.</p> : <div className="assessment-grid">{assessments.map(a => <article className="assessment-card" key={a.id}>
      <div className="card-meta"><span className="status-pill">Open assignment</span><span>{a.max_marks} marks</span></div>
      <h2>{a.title}</h2><p>{a.topics.join(' · ')}</p>
      <p className="muted">Due {new Date(a.due_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}</p>
      <Link className="primary" to={`/student/assessments/${a.id}`}>Open assessment <span aria-hidden="true">→</span></Link>
    </article>)}</div>}
  </main>;
}
export function AssessmentEditor() {
  const { assessmentId = '' } = useParams();
  return <AssessmentEditorLoader key={assessmentId} assessmentId={assessmentId} />;
}
function AssessmentEditorLoader({ assessmentId }: { assessmentId: string }) {
  const [loaded, setLoaded] = useState<{ assessment: Assessment; submission: Submission } | null>(null);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    Promise.all([studentApi.assessment(assessmentId), studentApi.start(assessmentId)]).then(([assessment, submission]) => { if (active) setLoaded({ assessment, submission }); }).catch(e => { if (active) setError(String(e.message)); });
    return () => { active = false; };
  }, [assessmentId, attempt]);
  if (error) return <main className="student-page"><Link to="/student">Back to assessments</Link><p role="alert">{error}</p><button onClick={() => { setError(''); setAttempt(a => a + 1); }}>Try again</button></main>;
  if (!loaded) return <main className="student-page" role="status">Opening your assessment...</main>;
  return <WritingSession key={loaded.submission.id} {...loaded} />;
}
function WritingSession({ assessment, submission }: { assessment: Assessment; submission: Submission }) {
  const [content, setContent] = useState(submission.content_md);
  const [status, setStatus] = useState('All changes saved');
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(submission.status !== 'draft');
  const [submitting, setSubmitting] = useState(false);
  const [recorder, setRecorder] = useState<ActivityRecorder | null>(null);
  const text = useRef(content);
  const saved = useRef(submission.content_md);
  const saving = useRef<Promise<void> | null>(null);
  const localKey = `vivagrade:draft:${submission.student_id}:${submission.id}`;
  useEffect(() => {
    if (submitted) return;
    const capture = new ActivityRecorder(submission.id);
    // The recorder owns browser listeners and must be disposed with this effect.
    // oxlint-disable-next-line react/set-state-in-effect
    setRecorder(capture);
    // Prior event batches already describe the local draft; never count recovery as typing.
    const recovered = localStorage.getItem(localKey);
    if (recovered !== null && recovered !== saved.current) {
      text.current = recovered;
      setContent(recovered);
      setStatus('Recovered local draft. Saving...');
    }
    const windowEvent = (event: Event) => capture.record(event.type === 'blur' ? 'blur' : 'focus');
    const visibility = () => capture.record(document.hidden ? 'hidden' : 'visible');
    const exit = () => capture.exit();
    window.addEventListener('blur', windowEvent); window.addEventListener('focus', windowEvent);
    document.addEventListener('visibilitychange', visibility); window.addEventListener('pagehide', exit);
    const timer = window.setInterval(() => { void capture.flush().catch(e => setError(`Writing activity could not be uploaded: ${e.message}`)); }, 3000);
    return () => {
      window.clearInterval(timer); window.removeEventListener('blur', windowEvent); window.removeEventListener('focus', windowEvent);
      document.removeEventListener('visibilitychange', visibility); window.removeEventListener('pagehide', exit);
      capture.exit();
    };
  }, [localKey, submission.id, submitted]);
  const save = useCallback(async () => {
    if (saving.current) await saving.current;
    if (saved.current === text.current) return;
    const snapshot = text.current;
    setStatus('Saving your answer...');
    const operation = studentApi.save(submission.id, snapshot).then(() => { saved.current = snapshot; setStatus(saved.current === text.current ? 'All changes saved' : 'Unsaved changes'); });
    saving.current = operation;
    try { await operation; } finally { if (saving.current === operation) saving.current = null; }
  }, [submission.id]);
  useEffect(() => {
    if (submitted || submitting) return;
    const timer = window.setTimeout(() => { void save().catch(e => { setStatus('Saved locally. Upload failed.'); setError(e.message); }); }, 1000);
    return () => window.clearTimeout(timer);
  }, [content, submitted, submitting, save]);
  const change = (value: string) => { text.current = value; setContent(value); localStorage.setItem(localKey, value); setStatus('Unsaved changes'); };
  async function submit() {
    setSubmitting(true); setError('');
    try {
      await save(); await recorder?.flush();
      await studentApi.submit(submission.id);
      setSubmitted(true); localStorage.removeItem(localKey);
    } catch (e) { setError(e instanceof Error ? e.message : 'Could not submit your answer.'); }
    finally { setSubmitting(false); }
  }
  return <main className="student-page editor-page">
    <Link className="back" to="/student">← All assessments</Link>
    <div className="editor-heading"><div><p className="eyebrow">YOUR ASSIGNMENT</p><h1>{assessment.title}</h1></div><span className="mark-label">{assessment.max_marks} marks</span></div>
    
    <section className="instructions markdown"><ReactMarkdown>{assessment.instructions_md}</ReactMarkdown>
      <div className="setting-row"><span>Strictness: {assessment.strictness.replaceAll('_', ' ')}</span><span>Viva: {assessment.viva_enabled ? `${Math.round(assessment.viva_weight * 100)}% of final grade` : 'off'}</span><span>AI use: {assessment.ai_policy.replaceAll('_', ' ')}</span></div>
      <details><summary>How your work is assessed</summary>{assessment.rubric?.criteria.map(c => <p key={c.id}><strong>{c.name} ({c.max_marks} marks).</strong> {c.description}</p>)}</details>
    </section>
    {submitted ? <section className="submission-done"><p className="eyebrow">SUBMITTED</p><h2>Your work is in.</h2><p>Your answer is locked. {assessment.viva_enabled ? 'The next step is a short viva about your own work.' : 'Your teacher will review your work.'}</p>{assessment.viva_enabled && <Link className="primary" to={`/student/submissions/${submission.id}/viva`}>Continue to viva</Link>} <Link to={`/student/submissions/${submission.id}/result`}>Check released result</Link><div className="markdown"><ReactMarkdown>{content}</ReactMarkdown></div></section> : <>
      <aside className="recording-notice"><strong>Writing process is recorded.</strong> Your teacher can review how this answer was written.
        <details><summary>What is recorded?</summary><p>Edits, pasted text, deletions, undo/redo, times, and whether this editor page loses focus or becomes hidden. We capture no typing outside this editor, screens or webcam. These are signals for teacher review and do not apply a mark penalty on their own.</p></details>
      </aside>
      {error && <div role="alert" className="error">{error} <button onClick={() => { void Promise.all([save(), recorder?.flush()]).then(() => setError('')).catch(e => setError(e.message)); }}>Retry save and upload</button></div>}
      <div className="writing-grid" inert={submitting}>
        <section className="writing-panel"><div className="panel-label">YOUR ANSWER <span>Markdown</span></div><Suspense fallback={<p role="status">Opening your editor...</p>}>{recorder && <MarkdownEditor initial={submission.content_md === content ? submission.content_md : (localStorage.getItem(localKey) ?? submission.content_md)} recorder={recorder} onChange={change} />}</Suspense></section>
        <section className="writing-panel"><div className="panel-label">LIVE PREVIEW</div><div className="markdown preview">{content ? <ReactMarkdown>{content}</ReactMarkdown> : <p className="muted">Your answer will appear here as you write.</p>}</div></section>
      </div>
      <footer className="save-bar"><div><span role="status">{submitting ? 'Saving and submitting your work...' : status}</span><span className="muted">{content.trim() ? content.trim().split(/\s+/).length : 0} words</span></div><button className="primary" disabled={submitting || !content.trim() || !recorder} onClick={() => void submit()}>{submitting ? 'Submitting...' : 'Submit answer'}</button></footer>
    </>}
  </main>;
}
