import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ApiError } from '../../api/client';
import { studentApi } from '../../api/student';
import type { Feedback, StudentResult } from '../../api/types';

export function FeedbackView({ feedback }: { feedback: Feedback }) {
  return <div className="feedback-grid"><section><h2>What went well</h2>{feedback.strengths.length ? feedback.strengths.map((s, i) => <article key={`${s.criterion_id}:${i}`}><p>{s.text}</p>{s.quote && <blockquote>{s.quote}</blockquote>}</article>) : <p>No strengths were included in this feedback.</p>}</section>
    <section><h2>What to improve</h2>{feedback.improvements.length ? feedback.improvements.map((s, i) => <article key={`${s.criterion_id}:${i}`}><p>{s.text}</p>{s.quote && <blockquote>{s.quote}</blockquote>}{s.hint && <p><strong>Hint:</strong> {s.hint}</p>}{feedback.mode === 'full' && s.explanation && <details><summary>Show explanation</summary><p>{s.explanation}</p></details>}</article>) : <p>No improvements were included in this feedback.</p>}</section>
    <section className="next-step"><h2>Your next step</h2><p>{feedback.next_step || 'Discuss your feedback with your teacher.'}</p></section></div>;
}
export function ResultView({ result }: { result: StudentResult }) {
  return <><section className="result-score"><div><h1>{result.final_with_grace.toFixed(1)} <small>of {result.max_marks}</small></h1><p>Final grade · {result.final_pct.toFixed(1)}%</p>{result.grace_marks > 0 && <p>Includes +{result.grace_marks.toFixed(1)} grace marks</p>}</div><div><h2>Understanding</h2>{result.understanding === null ? <p>Viva not taken</p> : <><meter min={0} max={1} value={result.understanding} aria-label={`Understanding ${Math.round(result.understanding * 100)} percent`} /><p>{Math.round(result.understanding * 100)}%</p></>}<p className="muted">Written work: {result.work_marks.toFixed(1)} of {result.max_marks}<br />Viva weight: {Math.round(result.viva_weight * 100)}%</p></div></section><FeedbackView feedback={result.feedback} /></>;
}
export function StudentResultPage() {
  const { submissionId = '' } = useParams();
  return <StudentResultLoader key={submissionId} submissionId={submissionId} />;
}
function StudentResultLoader({ submissionId }: { submissionId: string }) {
  const [result, setResult] = useState<StudentResult | null>(null);
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    studentApi.result(submissionId).then(data => { if (active) setResult(data); }).catch(e => {
      if (!active) return;
      if ((e instanceof ApiError || (e instanceof Error && 'code' in e)) && e.code === 'not_released') setPending(true);
      else setError(e.message);
    });
    return () => { active = false; };
  }, [submissionId, attempt]);
  return <main className="student-page"><Link to="/student">Back to my work</Link>
    {result ? <ResultView result={result} /> : pending ? <section><h1>Your result is being reviewed.</h1><p>Your teacher has not released your result yet.</p><button className="primary" onClick={() => { setPending(false); setAttempt(a => a + 1); }}>Check again</button></section> : error ? <div className="error" role="alert">{error} <button onClick={() => { setError(''); setAttempt(a => a + 1); }}>Retry</button></div> : <p role="status">Loading your result...</p>}
  </main>;
}
