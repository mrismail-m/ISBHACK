import { useEffect, useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { apiClient, USE_FIXTURES } from '../../api/client';
import { labApi } from '../../api/learning-lab';
import type { Assessment, LabReport, LabState } from '../../api/types';
import { Observation } from '../student/LearningLab';
import { labOutcome, levelLabels } from '../student/lab-display';
import '../student/learning-lab.css';

export function LearningLabReportPage() {
  const { id } = useParams();
  return <LearningLabReport key={id || 'default'} assessmentId={id} />;
}
function LearningLabReport({ assessmentId }: { assessmentId?: string }) {
  const navigate = useNavigate();
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [report, setReport] = useState<LabReport | null>(null);
  const [selected, setSelected] = useState<LabState | null>(null);
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    async function load() {
      const list = await apiClient<Assessment[]>('/assessments', { fixtureName: 'assessments' });
      if (!active) return;
      setAssessments(list);
      const actual = assessmentId || list[0]?.id;
      if (!actual) { setReport({ assessment_id: '', sessions: [] }); return; }
      const result = await labApi.report(actual);
      if (active) { setReport(result); setSelected(null); }
    }
    load().catch(e => { if (active) setError(e instanceof Error ? e.message : 'Could not load learning evidence.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [assessmentId, refresh]);
  const sessions = report?.sessions || [];
  const completed = sessions.filter(s => s.phase === 'complete');
  const improved = completed.filter(s => s.initial && s.final && s.final.level > s.initial.level);
  const followup = completed.filter(s => s.final && s.final.level < 2);
  const groups = new Map<string, LabState[]>();
  for (const session of sessions) {
    const key = session.concept;
    groups.set(key, [...(groups.get(key) || []), session]);
  }
  return <main className="lab-page"><div className="lab-topline"><Link to="/teacher">← My assignments</Link><span>{USE_FIXTURES || sessions.some(s => s.mode === 'fixture') ? 'Demo mode · sample feedback' : 'AI feedback for teacher review'}</span></div>
    <header className="lab-heading lab-heading-simple"><p className="lab-eyebrow">TEACHER · STUDENT PROGRESS</p><h1>What does your class need help with?</h1><p>Students answer a question, receive an explanation, then try a different question. Compare their answers to decide what to explain in your next lesson.</p></header>
    <div className="lab-controls"><label htmlFor="lab-assessment">Choose an assignment</label><select id="lab-assessment" value={report?.assessment_id || assessmentId || ''} onChange={e => navigate(`/teacher/assessments/${e.target.value}/learning-lab`)}>{assessments.map(a => <option value={a.id} key={a.id}>{a.title}</option>)}</select><button className="lab-primary" disabled={loading} onClick={() => { setLoading(true); setError(''); setRefresh(n => n + 1); }}>Refresh progress</button></div>
    {error && <div className="lab-error" role="alert">{error}</div>}
    {loading ? <section className="lab-card" role="status">Loading class learning evidence…</section> : !error && <>
      <div className="lab-stats">{[[sessions.length, 'Students started'], [completed.length, 'Students finished'], [improved.length, 'Improved after help'], [followup.length, 'Need more help']].map(([value, label]) => <div className="lab-stat" key={label}><strong>{value}</strong><span>{label}</span></div>)}</div>
      {!sessions.length ? <section className="lab-card"><h2>No practice answers yet.</h2><p>Ask students to open this assignment in <strong>My assignments</strong>. After submitting their work, they choose <strong>Start practice</strong>.</p><div className="lab-how"><div><b>Student answers</b><p>A short question checks how they use an idea from their work.</p></div><div><b>Student gets help</b><p>An explanation addresses what their answer missed.</p></div><div><b>You see progress</b><p>After the second answer, this page shows who improved and who needs help.</p></div></div><p><strong>Your next step:</strong> Ask students to complete the practice, then select Refresh progress.</p><Link className="lab-primary" to={`/teacher/assessments/${report?.assessment_id}`}>Open this assignment →</Link></section> : <>
        <div className="lab-next-action"><strong>Your next step</strong><p>{followup.length ? `Start with the ${followup.length} students who still need help. Open their answers below, then use the suggested explanation in your lesson.` : completed.length ? 'Read the first and second answers below to check the feedback. Students still practising will appear as In progress.' : 'Students are still practising. Read their first answers below, then refresh when they have finished.'}</p></div>
        <section className="lab-card"><span className="lab-kicker">WHAT TO EXPLAIN NEXT</span><h2>Ideas your students need help with</h2>{[...groups.entries()].map(([concept, rows]) => {
          const needing = rows.filter(s => s.final ? s.final.level < 2 : s.initial && s.initial.level < 2);
          return <div className="lab-teaching" key={concept}><h3>{concept}</h3><p>{needing.length} of {rows.length} students may need help; {rows.filter(s => s.phase !== 'complete').length} still in progress.</p>{needing[0] && <><p><strong>Suggested explanation to use in class:</strong> {(needing[0].final || needing[0].initial)?.teaching}</p><button className="lab-primary" onClick={() => setSelected(needing[0])}>Read this student’s answers →</button></>}</div>;
        })}</section>
        <section className="lab-card"><span className="lab-kicker">CHECK THE ACTUAL ANSWERS</span><h2>Student answers and progress</h2><div className="lab-evidence-wrap"><table className="lab-evidence"><thead><tr><th>Student</th><th>First answer</th><th>Answer after help</th><th>What to do next</th></tr></thead><tbody>{sessions.map((s, i) => <tr key={s.id}><td><button onClick={() => setSelected(s)}>Read Student {i + 1}’s answers ↗</button><br /><small>{s.mode === 'fixture' ? 'Demo practice' : 'Student practice'}</small></td><td>{s.initial ? levelLabels[s.initial.level] : 'Awaiting answer'}</td><td>{s.final ? levelLabels[s.final.level] : 'Still practising'}</td><td>{labOutcome(s)}</td></tr>)}</tbody></table></div><p className="lab-muted">Feedback describes these two answers. Review the answers before deciding what the student needs next. Practice does not change assignment grades.</p></section>
      </>}
    </>}
    {selected && <section ref={node => { node?.scrollIntoView({ block: 'start' }); }} className="lab-card" aria-label="Selected learner evidence"><div className="lab-controls"><h2>What did this student understand?</h2><button className="lab-primary" onClick={() => setSelected(null)}>Close answers</button></div><p>{selected.concept} · Submission {selected.submission_id}</p><p className="lab-kicker">THE IDEA IN THEIR ASSIGNMENT</p><blockquote className="lab-quote">{selected.anchor_quote}</blockquote><div className="lab-comparison"><section><h3>First question</h3><p>{selected.challenge.scenario}</p><p><strong>{selected.challenge.question}</strong></p><p className="lab-quote">{selected.initial_answer || 'Not answered yet.'}</p>{selected.initial && <Observation value={selected.initial} />}</section><section><h3>Question after help</h3><p>{selected.recovery?.scenario || 'The student has not reached the second question yet.'}</p><p><strong>{selected.recovery?.question}</strong></p><p className="lab-quote">{selected.recovery_answer || 'Not answered yet.'}</p>{selected.final && <Observation value={selected.final} />}</section></div>{selected.initial && <div className="lab-teaching"><h3>The help the student received</h3><p>{selected.initial.teaching}</p></div>}<Link to={`/teacher/submissions/${selected.submission_id}/review`}>Review the original assignment →</Link></section>}
  </main>;
}
