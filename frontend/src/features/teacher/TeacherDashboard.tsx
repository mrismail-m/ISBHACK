import roster from '../../../../fixtures/demo/roster.json';
import { ActivityInsights } from '../insights/ActivityInsights';
import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../../api/client';
import type { 
  AssessmentStats, ClassPerformance, AttentionStudent, 
  GracePreview, GraceState, OverrideStats 
} from '../../api/types';

export function ClassroomDashboard() {
  const [loadError, setLoadError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [selectedStudent, setSelectedStudent] = useState(roster[0].user_id);
  const [performance, setPerformance] = useState<ClassPerformance | null>(null);
  const [attention, setAttention] = useState<AttentionStudent[]>([]);

  useEffect(() => {
    let active = true;
    Promise.all([
      apiClient<ClassPerformance>('/classrooms/cl_1/performance'),
      apiClient<AttentionStudent[]>('/classrooms/cl_1/attention'),
    ]).then(([data, students]) => {
      if (active) { setPerformance(data); setAttention(students); }
    }).catch(error => { if (active) setLoadError(error instanceof Error ? error.message : 'Dashboard could not load.'); });
    return () => { active = false; };
  }, [attempt]);

  if (loadError) return <main className="student-page" role="alert">{loadError} <button onClick={() => { setLoadError(''); setAttempt(value => value + 1); }}>Retry dashboard</button></main>;
  if (!performance) return <div className="p-8 text-center text-slate-500" role="status">Loading classroom dashboard...</div>;

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <div>
        <Link to="/teacher" className="text-blue-600 hover:underline mb-4 inline-block">&larr; Back to Assessments</Link>
        <h2 className="text-3xl font-bold text-slate-800">Classroom Dashboard</h2>
        <section className="lab-feature-banner"><h2>Student learning progress</h2><p>See who improved after an explanation and who needs more help. Read their answers to decide what to teach next.</p><Link to="/teacher/learning-lab">See student progress →</Link></section>

      </div>

      <section className="bg-white p-6 rounded-lg border border-slate-200">
        <h3 className="text-xl font-semibold mb-4">Student writing evidence</h3>
        <label>Student <select className="border p-2 rounded max-w-full" value={selectedStudent} onChange={e => setSelectedStudent(e.target.value)}>{roster.map(row => <option key={row.user_id} value={row.user_id}>{row.reg_no} · {row.name}</option>)}</select></label>
        <p className="mt-3"><Link to={`/teacher/submissions/demo_s_3_${roster.findIndex(row => row.user_id === selectedStudent) + 1}/review`}>Open full review and rubric</Link></p>
        <ActivityInsights key={selectedStudent} submissionId={`demo_s_3_${roster.findIndex(row => row.user_id === selectedStudent) + 1}`} />
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
          <h3 className="font-semibold text-lg border-b pb-2 mb-4">Class Trend (Avg %)</h3>
          <div className="flex items-end gap-3" style={{ height: 200 }} role="img" aria-label="Class average percentages by completed assessment">
            {performance.assessments.map(a => (
              <div key={a.assessment_id} className="flex-1 min-w-0 flex flex-col justify-end items-center group relative">
                <span className="text-sm font-semibold mb-2">{a.avg_pct == null ? "Pending" : `${Math.round(a.avg_pct)}%`}</span>
                <div 
                  className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600" 
                  style={{ height: `${Math.max(2, Math.min(100, a.avg_pct ?? 0) * 1.4)}px` }}
                ></div>
                <div className="text-xs text-slate-500 mt-2 truncate w-full text-center">{a.title}</div>
                
                {/* Tooltip */}
                <div className="absolute bottom-full mb-2 opacity-0 group-hover:opacity-100 bg-slate-800 text-white text-xs rounded py-1 px-2 pointer-events-none transition-opacity whitespace-nowrap">
                  {a.title}<br/>Avg: {Math.round(a.avg_pct || 0)}%
                </div>
              </div>
            ))}
            {!performance.assessments.length && <p className="text-slate-500">No completed assessment scores yet.</p>}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
          <h3 className="font-semibold text-lg border-b pb-2 mb-4 text-amber-700">Needs Attention</h3>
          {attention.length === 0 ? (
            <p className="text-sm text-slate-500">No attention flags from released results.</p>
          ) : (
            <ul className="space-y-4">
              {attention.map(stu => (
                <li key={stu.student_id} className="p-3 bg-amber-50 rounded border border-amber-100">
                  <div className="font-medium text-amber-900">{stu.name}</div>
                  <div className="flex gap-2 mt-1">
                    {stu.reasons.map(r => (
                      <span key={r} className="text-xs bg-amber-200 text-amber-800 px-2 py-0.5 rounded capitalize">
                        {r.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                  <div className="text-xs text-slate-600 mt-2">
                    Recent scores: {stu.recent_scores_pct.map(s => `${Math.round(s)}%`).join(', ')}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

export function AssessmentDashboard({ assessmentId }: { assessmentId: string }) {
  const [stats, setStats] = useState<AssessmentStats | null>(null);
  const [overrideStats, setOverrideStats] = useState<OverrideStats | null>(null);
  const [graceState, setGraceState] = useState<GraceState | null>(null);

  const [previewMarks, setPreviewMarks] = useState(0);
  const [gracePreview, setGracePreview] = useState<GracePreview | null>(null);
  const [graceReason, setGraceReason] = useState("");

  const refreshData = useCallback(() => {
    apiClient<AssessmentStats>(`/assessments/${assessmentId}/stats`).then(setStats).catch(console.error);
    apiClient<OverrideStats>(`/assessments/${assessmentId}/override-stats`).then(setOverrideStats).catch(console.error);
    // There isn't a GET endpoint for grace state alone in contract.
    // Grace state is returned from apply/undo. We might not have it until applied.
  }, [assessmentId]);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  if (!stats) return <div className="py-8 text-center text-slate-500 text-sm">Loading assessment stats...</div>;

  const handlePreviewGrace = async () => {
    if (!previewMarks) return;
    try {
      const res = await apiClient<GracePreview>(`/assessments/${assessmentId}/grace/preview`, {
        method: 'POST',
        body: JSON.stringify({ marks: Number(previewMarks), reason: graceReason })
      });
      setGracePreview(res);
    } catch (e) {
      console.error(e);
      alert("Failed to preview grace marks");
    }
  };

  const handleApplyGrace = async () => {
    try {
      const res = await apiClient<GraceState>(`/assessments/${assessmentId}/grace/apply`, {
        method: 'POST',
        body: JSON.stringify({ marks: Number(previewMarks), reason: graceReason })
      });
      setGraceState(res);
      setGracePreview(null);
      setPreviewMarks(0);
      setGraceReason("");
      refreshData();
    } catch (e) {
      console.error(e);
      alert("Failed to apply grace marks");
    }
  };

  const handleUndoGrace = async (entryId?: string) => {
    try {
      const res = await apiClient<GraceState>(`/assessments/${assessmentId}/grace/undo`, {
        method: 'POST',
        body: JSON.stringify({ entry_id: entryId })
      });
      setGraceState(res);
      refreshData();
    } catch (e) {
      console.error(e);
      alert("Failed to undo grace marks");
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow border border-slate-200">
          <div className="text-sm text-slate-500 font-medium">Submissions</div>
          <div className="text-2xl font-bold text-slate-800">{stats.submitted} / {stats.enrolled}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border border-slate-200">
          <div className="text-sm text-slate-500 font-medium">Graded vs Pending</div>
          <div className="text-2xl font-bold text-slate-800">{stats.graded} <span className="text-sm font-normal text-slate-400">graded</span> / {Math.max(0, stats.submitted - stats.graded)} <span className="text-sm font-normal text-slate-400">awaiting grading</span><p className="text-xs font-normal text-slate-500 mt-2">{stats.pending_review} awaiting teacher review</p></div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border border-slate-200">
          <div className="text-sm text-slate-500 font-medium">Average Score</div>
          <div className="text-2xl font-bold text-slate-800">{stats.avg_pct != null ? `${Math.round(stats.avg_pct)}%` : '-'}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border border-slate-200">
          <div className="text-sm text-slate-500 font-medium">Pass Rate</div>
          <div className="text-2xl font-bold text-slate-800">{stats.pass_rate_pct != null ? `${Math.round(stats.pass_rate_pct)}%` : '-'}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
          <h3 className="font-semibold text-lg border-b pb-2 mb-4">Score Distribution</h3>
          <div className="flex items-end gap-1" style={{ height: 200 }} role="img" aria-label="Number of graded submissions in each score range">
            {stats.histogram.map(bin => {
              const height = (bin.count / Math.max(1, ...stats.histogram.map(row => row.count))) * 140;
              return (
                <div key={bin.bin} className="flex-1 min-w-0 flex flex-col justify-end items-center group relative">
                  <span className="text-xs font-semibold mb-1">{bin.count}</span>
                  <div className="w-full bg-indigo-500 rounded-t" style={{ height: `${Math.max(2, height)}px` }}></div>
                  <div className="text-[10px] text-slate-400 mt-1">{bin.bin}</div>
                  <div className="absolute bottom-full mb-1 opacity-0 group-hover:opacity-100 bg-slate-800 text-white text-xs rounded py-1 px-2">{bin.count} students</div>
                </div>
              );
            })}
          </div>
          {stats.graded === 0 && <p className="text-sm text-slate-500 mt-2">Scores will appear after grading.</p>}
        </div>

        <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
          <h3 className="font-semibold text-lg border-b pb-2 mb-4">Topic Performance</h3>
          <div className="space-y-4">
            {stats.topic_averages.map(t => (
              <div key={t.topic}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-slate-700 capitalize">{t.topic}</span>
                  <span className="text-slate-500">{Math.round(t.avg_pct)}%</span>
                </div>
                <div className="w-full bg-slate-100 rounded h-2">
                  <div className="bg-blue-500 h-2 rounded" style={{ width: `${t.avg_pct}%` }}></div>
                </div>
              </div>
            ))}
            {stats.topic_averages.length === 0 && <div className="text-slate-500 text-sm">No topics available</div>}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
          <h3 className="font-semibold text-lg border-b pb-2 mb-4">Override Stats</h3>
          {overrideStats ? (
            <div>
              <div className="flex justify-between mb-4">
                <div>
                  <div className="text-xl font-bold text-slate-800">{Math.round(overrideStats.override_rate_pct)}%</div>
                  <div className="text-xs text-slate-500">Override Rate</div>
                </div>
                <div>
                  <div className="text-xl font-bold text-slate-800">{overrideStats.mean_signed_delta_marks > 0 ? '+' : ''}{overrideStats.mean_signed_delta_marks.toFixed(1)}</div>
                  <div className="text-xs text-slate-500">Avg Delta</div>
                </div>
              </div>
              {overrideStats.overridden === 0 && <p className="text-sm text-slate-500 mb-3">No teacher adjustments recorded yet.</p>}
              <div className="space-y-2">
                {overrideStats.by_criterion.map(c => (
                  <div key={c.criterion_id} className="flex justify-between text-sm bg-slate-50 p-2 rounded">
                    <span className="font-medium text-slate-700">{c.criterion_id}</span>
                    <span className="text-slate-500">{Math.round(c.override_rate_pct)}% rate ({c.mean_signed_delta_marks > 0 ? '+' : ''}{c.mean_signed_delta_marks.toFixed(1)} marks)</span>
                  </div>
                ))}
              </div>
            </div>
          ) : <div className="text-sm text-slate-500">Loading overrides...</div>}
        </div>

        <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
          <h3 className="font-semibold text-lg border-b pb-2 mb-4">Grace Marks</h3>
          <div className="space-y-4">
            <div className="flex gap-2">
              <input 
                type="number" 
                placeholder="Marks" 
                value={previewMarks} 
                onChange={e => setPreviewMarks(Number(e.target.value))}
                className="border rounded p-2 text-sm w-24 outline-none focus:ring-1 focus:ring-blue-500"
              />
              <input 
                type="text" 
                placeholder="Reason (optional)" 
                value={graceReason} 
                onChange={e => setGraceReason(e.target.value)}
                className="border rounded p-2 text-sm flex-1 outline-none focus:ring-1 focus:ring-blue-500"
              />
              <button onClick={handlePreviewGrace} className="bg-indigo-100 hover:bg-indigo-200 text-indigo-700 px-4 py-2 rounded text-sm font-medium transition-colors">
                Preview
              </button>
            </div>
            
            {gracePreview && (
              <div className="p-4 bg-indigo-50 border border-indigo-100 rounded text-sm">
                <p className="font-semibold text-indigo-900 mb-2">Preview Impact</p>
                <ul className="space-y-1 text-indigo-800">
                  <li><strong>Affected students:</strong> {gracePreview.affected_students}</li>
                  <li><strong>Capped at max marks:</strong> {gracePreview.capped_count}</li>
                  <li><strong>Avg Score:</strong> {Math.round(gracePreview.before.avg_pct)}% &rarr; {Math.round(gracePreview.after.avg_pct)}%</li>
                  <li><strong>Pass Rate:</strong> {Math.round(gracePreview.before.pass_rate_pct)}% &rarr; {Math.round(gracePreview.after.pass_rate_pct)}%</li>
                </ul>
                <div className="mt-3 flex gap-2">
                  <button onClick={handleApplyGrace} className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1.5 rounded font-medium transition-colors shadow-sm">
                    Apply Grace
                  </button>
                  <button onClick={() => setGracePreview(null)} className="text-indigo-600 hover:underline px-3 py-1.5">
                    Cancel
                  </button>
                </div>
              </div>
            )}
            
            {/* Show recent grace application. To simplify, we'll fetch /undo if there is state */}
            {graceState && graceState.entries.some(e => !e.undone_at) && (
              <div className="mt-4 border-t pt-4">
                <div className="text-sm font-medium text-slate-700 mb-2">Active Grace Marks</div>
                {graceState.entries.filter(e => !e.undone_at).map(e => (
                  <div key={e.id} className="flex justify-between items-center text-sm p-2 bg-slate-50 rounded">
                    <span>+{e.marks} {e.reason ? `(${e.reason})` : ''}</span>
                    <button onClick={() => handleUndoGrace(e.id)} className="text-red-600 hover:underline">Undo</button>
                  </div>
                ))}
              </div>
            )}
            
            {(!graceState || !graceState.entries.some(e => !e.undone_at)) && stats.grace_marks_applied > 0 && (
              <div className="mt-4 pt-4 border-t flex justify-between items-center">
                 <span className="text-sm text-slate-600">Total applied: +{stats.grace_marks_applied}</span>
                 <button onClick={() => handleUndoGrace()} className="text-red-600 hover:underline text-sm">Undo Latest</button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
