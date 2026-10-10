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
  return <main className="lab-page"><div className="lab-topline"><Link to="/teacher/classroom">← Teacher classroom</Link><span>{USE_FIXTURES || sessions.some(s => s.mode === 'fixture') ? 'Includes offline fixture evidence' : 'AI observations · teacher review'}</span></div>
    <header className="lab-heading"><p className="lab-eyebrow">LEARNING LAB · TEACHER VIEW</p><h1>See what changed.<br /><em>Decide what to teach next.</em></h1><p>Two different scenarios, one targeted explanation, and the reasoning before and after.</p></header>
    <div className="lab-controls"><label htmlFor="lab-assessment">Assessment</label><select id="lab-assessment" value={report?.assessment_id || assessmentId || ''} onChange={e => navigate(`/teacher/assessments/${e.target.value}/learning-lab`)}>{assessments.map(a => <option value={a.id} key={a.id}>{a.title}</option>)}</select><button className="lab-primary" disabled={loading} onClick={() => { setLoading(true); setError(''); setRefresh(n => n + 1); }}>Refresh evidence</button></div>
    {error && <div className="lab-error" role="alert">{error}</div>}
    {loading ? <section className="lab-card" role="status">Loading class learning evidence…</section> : !error && <>
      <div className="lab-stats">{[[sessions.length, 'Experiments started'], [completed.length, 'Both attempts completed'], [improved.length, 'Higher level on second attempt'], [followup.length, 'Need another teaching step']].map(([value, label]) => <div className="lab-stat" key={label}><strong>{value}</strong><span>{label}</span></div>)}</div>
      {!sessions.length ? <section className="lab-card"><h2>The first experiment starts with a student.</h2><p>After submitting an assignment, the student opens Learning Lab, answers a changed-condition question, reads a targeted explanation, and tries a different scenario. Their saved evidence appears here.</p><p className="lab-muted">No student outcomes are pre-filled. Offline fixture sessions appear only after someone completes the practice.</p></section> : <>
        <section className="lab-card"><span className="lab-kicker">TEACHING PRIORITIES</span><h2>Where another explanation could help.</h2>{[...groups.entries()].map(([concept, rows]) => {
          const needing = rows.filter(s => s.final ? s.final.level < 2 : s.initial && s.initial.level < 2);
          return <div className="lab-teaching" key={concept}><h3>{concept}</h3><p>{needing.length} of {rows.length} observed sessions currently suggest follow-up; {rows.filter(s => s.phase !== 'complete').length} still in progress.</p>{needing[0] && <><p><strong>Suggested explanation for teacher review:</strong> {(needing[0].final || needing[0].initial)?.teaching}</p><button className="lab-primary" onClick={() => setSelected(needing[0])}>Inspect supporting answers →</button></>}</div>;
        })}</section>
        <section className="lab-card"><span className="lab-kicker">OBSERVATIONS, WITH THE ANSWERS BEHIND THEM</span><h2>Learning evidence</h2><div className="lab-evidence-wrap"><table className="lab-evidence"><thead><tr><th>Submission</th><th>Before explanation</th><th>New scenario</th><th>Next step</th></tr></thead><tbody>{sessions.map((s, i) => <tr key={s.id}><td><button onClick={() => setSelected(s)}>Learner {i + 1} ↗</button><br /><small>{s.mode === 'fixture' ? 'Fixture session' : 'Live session'}</small></td><td>{s.initial ? levelLabels[s.initial.level] : 'Awaiting answer'}</td><td>{s.final ? levelLabels[s.final.level] : 'Awaiting second attempt'}</td><td>{labOutcome(s)}</td></tr>)}</tbody></table></div><p className="lab-muted">These levels describe responses to two scenarios. They do not diagnose authorship or establish lasting mastery. Assignment grades stay separate.</p></section>
      </>}
    </>}
    {selected && <section ref={node => { node?.scrollIntoView({ block: 'start' }); }} className="lab-card" aria-label="Selected learner evidence"><div className="lab-controls"><h2>Follow the reasoning.</h2><button className="lab-primary" onClick={() => setSelected(null)}>Close evidence</button></div><p>{selected.concept} · Submission {selected.submission_id}</p><p className="lab-kicker">ASSIGNMENT ANCHOR · VERIFIED QUOTE</p><blockquote className="lab-quote">{selected.anchor_quote}</blockquote><div className="lab-comparison"><section><h3>First scenario</h3><p>{selected.challenge.scenario}</p><p><strong>{selected.challenge.question}</strong></p><p className="lab-quote">{selected.initial_answer || 'Not answered yet.'}</p>{selected.initial && <Observation value={selected.initial} />}</section><section><h3>Different scenario</h3><p>{selected.recovery?.scenario || 'Available after the first answer.'}</p><p><strong>{selected.recovery?.question}</strong></p><p className="lab-quote">{selected.recovery_answer || 'Not answered yet.'}</p>{selected.final && <Observation value={selected.final} />}</section></div>{selected.initial && <div className="lab-teaching"><h3>The explanation the student received</h3><p>{selected.initial.teaching}</p></div>}<Link to={`/teacher/submissions/${selected.submission_id}/review`}>Review the original assignment →</Link></section>}
  </main>;
}
