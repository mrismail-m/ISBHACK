import roster from '../../../../fixtures/demo/roster.json';
import { Routes, Route, Link, useNavigate, useParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { TeacherReviewDetail } from './TeacherReviewDetail';
import { LearningLabReportPage } from './LearningLabReport';
import { TrustReportPage } from './TrustReportPage';
import { ClassroomDashboard, AssessmentDashboard } from './TeacherDashboard';
import { apiClient } from '../../api/client';
import type { Assessment, SubmissionRow, Rubric, StrictnessPreview } from '../../api/types';

export function TeacherApp() {
  return (
    <Routes>
      <Route path="/" element={<AssessmentList />} />
      <Route path="/classroom" element={<ClassroomDashboard />} />
      <Route path="/learning-lab" element={<LearningLabReportPage />} />
      <Route path="/assessments/:id/learning-lab" element={<LearningLabReportPage />} />
      <Route path="/trust-report" element={<TrustReportPage />} />
      <Route path="/assessments/new" element={<AssessmentSettings isNew />} />
      <Route path="/assessments/:id" element={<AssessmentDetail />} />
      <Route path="/assessments/:id/settings" element={<AssessmentSettings />} />
      <Route path="/submissions/:submissionId/review" element={<TeacherReviewDetail />} />
    </Routes>
  );
}

function AssessmentList() {
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    apiClient<Assessment[]>('/assessments', { fixtureName: 'assessments' })
      .then(setAssessments)
      .catch(console.error);
  }, []);

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-bold text-slate-800">My assignments</h2>
        <div className="flex gap-2">
          <button 
            onClick={() => navigate('/teacher/trust-report')}
            className="bg-indigo-100 hover:bg-indigo-200 text-indigo-700 px-4 py-2 rounded shadow transition-colors font-medium"
          >
            Trust Report
          </button>
          <button 
            onClick={() => navigate('/teacher/classroom')}
            className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded shadow transition-colors"
          >
            Classroom Dashboard
          </button>
          <button 
            onClick={() => navigate('/teacher/assessments/new')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded shadow transition-colors"
          >
            + New Assessment
          </button>
        </div>
      </div>
      
      <section className="lab-feature-banner"><h2>Find out what your class needs help with.</h2><p>Students submit their work, answer a practice question, get an explanation, and try again. You see who improved and who needs another explanation.</p><div className="lab-how"><div><b>1. Set an assignment</b><p>Create an assignment or choose one below.</p></div><div><b>2. Students practise</b><p>After submitting, students answer two questions with help in between.</p></div><div><b>3. Plan your next lesson</b><p>Open learning progress and read the answers of students who need help.</p></div></div><Link to="/teacher/learning-lab">See student learning progress →</Link></section>
      <div className="bg-white rounded-lg shadow border border-slate-200 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="p-4 text-sm font-semibold text-slate-600">Title</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Status</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Due</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Max Marks</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Learning progress</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {assessments.map(a => (
              <tr key={a.id} className="hover:bg-slate-50 cursor-pointer transition-colors" onClick={() => navigate(`/teacher/assessments/${a.id}`)}>
                <td className="p-4 font-medium text-slate-900">{a.title}</td>
                <td className="p-4">
                  <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                    a.status === 'open' ? 'bg-green-100 text-green-700' : 
                    a.status === 'closed' ? 'bg-slate-100 text-slate-700' : 
                    'bg-amber-100 text-amber-700'
                  }`}>
                    {a.status}
                  </span>
                </td>
                <td className="p-4 text-sm text-slate-600">{new Date(a.due_at).toLocaleDateString()}</td>
                <td className="p-4 text-sm text-slate-600">{a.max_marks}</td>
                <td className="p-4"><Link className="lab-table-action" to={`/teacher/assessments/${a.id}/learning-lab`} onClick={e => e.stopPropagation()}>View student progress →</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
        {assessments.length === 0 && (
          <div className="p-8 text-center text-slate-500">No assessments found.</div>
        )}
      </div>
    </div>
  );
}

function AssessmentDetail() {
  const { id } = useParams<{ id: string }>();
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [submissions, setSubmissions] = useState<SubmissionRow[]>([]);
  const [blindMode, setBlindMode] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (id) {
      apiClient<Assessment>(`/assessments/${id}`, { fixtureName: 'assessment_a1' })
        .then(setAssessment)
        .catch(console.error);
      apiClient<SubmissionRow[]>(`/assessments/${id}/submissions`, { fixtureName: 'submissions_a1' })
        .then(setSubmissions)
        .catch(console.error);
    }
  }, [id]);

  if (!assessment) return <div className="p-8 text-center text-slate-500">Loading...</div>;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <Link to="/teacher" className="text-blue-600 hover:underline mb-4 inline-block">&larr; Back to Assessments</Link>
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-3xl font-bold text-slate-800">{assessment.title}</h2>
          <p className="text-slate-500 mt-1 capitalize text-sm">Status: {assessment.status}</p>
        </div>
        <div className="flex gap-2">
          {assessment.status === 'draft' && (
            <button 
              onClick={() => {
                apiClient(`/assessments/${id}/publish`, { method: 'POST' }).then(() => window.location.reload());
              }}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded shadow transition-colors"
            >
              Publish
            </button>
          )}
          {assessment.status === 'open' && (
            <button 
              onClick={() => {
                apiClient(`/assessments/${id}/close`, { method: 'POST' }).then(() => window.location.reload());
              }}
              className="bg-slate-800 hover:bg-slate-900 text-white px-4 py-2 rounded shadow transition-colors"
            >
              Close
            </button>
          )}
          <button 
            onClick={() => navigate(`/teacher/assessments/${id}/settings`)}
            className="bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 px-4 py-2 rounded shadow-sm transition-colors"
          >
            Settings
          </button>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow border border-slate-200 mb-6">
        <h3 className="font-semibold text-lg mb-2">Instructions</h3>
        <p className="text-slate-600 whitespace-pre-wrap">{assessment.instructions_md}</p>
      </div>

      <div className="mb-8 border-t border-slate-200 pt-6">
        <AssessmentDashboard assessmentId={id!} />
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
        <h3 className="font-semibold text-lg mb-4">Configuration Summary</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><span className="text-slate-500 block">Strictness</span> <span className="font-medium capitalize">{assessment.strictness}</span></div>
          <div><span className="text-slate-500 block">AI Policy</span> <span className="font-medium capitalize">{assessment.ai_policy.replace(/_/g, ' ')}</span></div>
          <div><span className="text-slate-500 block">Viva Enabled</span> <span className="font-medium">{assessment.viva_enabled ? 'Yes' : 'No'}</span></div>
          {assessment.viva_enabled && <div><span className="text-slate-500 block">Viva Weight</span> <span className="font-medium">{assessment.viva_weight * 100}%</span></div>}
          <div><span className="text-slate-500 block">Feedback Mode</span> <span className="font-medium capitalize">{assessment.feedback_mode}</span></div>
          <div><span className="text-slate-500 block">Release Mode</span> <span className="font-medium capitalize">{assessment.release_mode.replace(/_/g, ' ')}</span></div>
        </div>
      </div>

      <div className="mt-8 bg-white rounded-lg shadow border border-slate-200 overflow-x-auto">
        <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
          <h3 className="font-semibold text-lg text-slate-800">Review Queue</h3>
          <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
            <input type="checkbox" checked={blindMode} onChange={e => setBlindMode(e.target.checked)} className="rounded text-blue-600 focus:ring-blue-500" />
            Blind Review Mode
          </label>
        </div>
        <table className="w-full text-left">
          <thead className="bg-slate-100 border-b border-slate-200">
            <tr>
              <th className="p-3 text-sm font-semibold text-slate-600">Student</th>
              <th className="p-3 text-sm font-semibold text-slate-600">Status</th>
              <th className="p-3 text-sm font-semibold text-slate-600">AI Score</th>
              <th className="p-3 text-sm font-semibold text-slate-600">Blended Score</th>
              <th className="p-3 text-sm font-semibold text-slate-600">Understanding</th>
              <th className="p-3 text-sm font-semibold text-slate-600">Flags</th>
              <th className="p-3 text-sm font-semibold text-slate-600 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {[...submissions].sort((a, b) => Number(b.ai_total != null) - Number(a.ai_total != null)).map(sub => (
              <tr key={sub.submission_id} className="hover:bg-slate-50 transition-colors">
                <td className="p-3 font-medium text-slate-900">{blindMode ? sub.label : <>{sub.student_name}<small className="block text-slate-500">{roster.find(row => row.name === sub.student_name)?.reg_no}</small></>}</td>
                <td className="p-3 text-sm capitalize">{sub.status.replace('_', ' ')}</td>
                <td className="p-3 text-sm">{sub.ai_total != null ? `${sub.ai_total}/${sub.max_marks}` : "Awaiting grading"}</td>
                <td className="p-3 text-sm font-medium">{sub.score_pct != null ? `${sub.score_pct.toFixed(1)}% (${sub.score_is_final ? 'final' : 'provisional'})` : 'Awaiting grading'}</td>
                <td className="p-3 text-sm">{sub.understanding != null ? `${Math.round(sub.understanding * 100)}%` : (assessment.viva_enabled ? "Awaiting viva" : "Not enabled")}</td>
                <td className="p-3 text-xs">
                  {sub.flags.map(f => (
                    <span key={f} className="inline-block bg-red-100 text-red-700 px-1.5 py-0.5 rounded mr-1 mb-1 capitalize">
                      {f.replace('_', ' ')}
                    </span>
                  ))}
                  {sub.flags.length === 0 && <span className="text-slate-400">None</span>}
                </td>
                <td className="p-3 text-right">
                  <button disabled={sub.ai_total == null} onClick={() => navigate(`/teacher/submissions/${sub.submission_id}/review`)} className="text-blue-600 hover:text-blue-800 font-medium text-sm">
                    {sub.ai_total == null ? "Awaiting grading" : "Review →"}
                  </button>
                </td>
              </tr>
            ))}
            {submissions.length === 0 && (
              <tr><td colSpan={7} className="p-6 text-center text-slate-500">No submissions yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AssessmentSettings({ isNew = false }: { isNew?: boolean }) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [formData, setFormData] = useState<Partial<Assessment>>({
    title: '',
    kind: 'assignment',
    instructions_md: '',
    max_marks: 20,
    pass_mark_pct: 50,
    strictness: 'normal',
    viva_enabled: true,
    viva_weight: 0.3,
    viva_question_count: 3,
    viva_time_limit_s: 90,
    feedback_mode: 'full',
    release_mode: 'after_approval',
    ai_policy: 'allowed_with_disclosure',
    paste_flag_chars: 500,
    topics: [],
    classroom_id: 'cl_1' // default
  });

  const [previewText, setPreviewText] = useState('');
  const [strictnessPreview, setStrictnessPreview] = useState<StrictnessPreview | null>(null);
  const [isDrafting, setIsDrafting] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);

  useEffect(() => {
    if (!isNew && id) {
      apiClient<Assessment>(`/assessments/${id}`, { fixtureName: 'assessment_a1' })
        .then(setFormData)
        .catch(console.error);
    }
  }, [id, isNew]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (isNew) {
        const res = await apiClient<Assessment>('/assessments', { method: 'POST', body: JSON.stringify(formData) });
        navigate(`/teacher/assessments/${res.id}`);
      } else {
        const res = await apiClient<Assessment>(`/assessments/${id}`, { method: 'PATCH', body: JSON.stringify(formData) });
        navigate(`/teacher/assessments/${res.id}`);
      }
    } catch (err) {
      console.error(err);
      alert('Failed to save assessment');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const value = e.target.type === 'checkbox' ? (e.target as HTMLInputElement).checked : 
                  e.target.type === 'number' ? Number(e.target.value) : e.target.value;
    setFormData({ ...formData, [e.target.name]: value });
  };

  const handleDraftRubric = async () => {
    if (!id) return alert('Save assessment first');
    setIsDrafting(true);
    try {
      const res = await apiClient<Rubric>(`/assessments/${id}/rubric/draft`, { method: 'POST', body: JSON.stringify({ notes: formData.instructions_md }) });
      setFormData(prev => ({ ...prev, rubric: res }));
    } catch (e) {
      console.error(e);
      alert('Failed to draft rubric');
    } finally {
      setIsDrafting(false);
    }
  };

  const handlePreviewStrictness = async () => {
    if (!id || !previewText) return;
    setIsPreviewing(true);
    try {
      const res = await apiClient<StrictnessPreview>(`/assessments/${id}/strictness/preview`, { method: 'POST', body: JSON.stringify({ answer_text: previewText }) });
      setStrictnessPreview(res);
    } catch (e) {
      console.error(e);
      alert('Failed to preview strictness');
    } finally {
      setIsPreviewing(false);
    }
  };

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <Link to={isNew ? "/teacher" : `/teacher/assessments/${id}`} className="text-blue-600 hover:underline mb-4 inline-block">&larr; Back</Link>
      <h2 className="text-3xl font-bold text-slate-800 mb-6">{isNew ? 'New Assessment' : 'Assessment Settings'}</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6 bg-white p-6 rounded-lg shadow border border-slate-200">
        
        <div className="space-y-4">
          <h3 className="font-semibold text-lg border-b pb-2">Basic Info</h3>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Title</label>
            <input required name="title" value={formData.title} onChange={handleChange} className="w-full border border-slate-300 rounded p-2 focus:ring focus:ring-blue-200 focus:border-blue-500 outline-none" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Kind</label>
            <select name="kind" value={formData.kind} onChange={handleChange} className="w-full border border-slate-300 rounded p-2 focus:ring focus:ring-blue-200 outline-none">
              <option value="assignment">Assignment</option>
              <option value="quiz">Quiz</option>
              <option value="exam">Exam</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Instructions</label>
            <textarea required rows={4} name="instructions_md" value={formData.instructions_md} onChange={handleChange} className="w-full border border-slate-300 rounded p-2 focus:ring focus:ring-blue-200 outline-none" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Max Marks</label>
              <input type="number" required name="max_marks" value={formData.max_marks} onChange={handleChange} className="w-full border border-slate-300 rounded p-2 focus:ring outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Pass Mark %</label>
              <input type="number" required name="pass_mark_pct" value={formData.pass_mark_pct} onChange={handleChange} className="w-full border border-slate-300 rounded p-2 focus:ring outline-none" />
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="font-semibold text-lg border-b pb-2">Policies & AI</h3>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">AI Grading Strictness</label>
            <select name="strictness" value={formData.strictness} onChange={handleChange} className="w-full border border-slate-300 rounded p-2 focus:ring outline-none">
              <option value="lenient">Lenient</option>
              <option value="normal">Normal</option>
              <option value="strict">Strict</option>
              <option value="very_strict">Very Strict</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">AI Usage Policy</label>
            <select name="ai_policy" value={formData.ai_policy} onChange={handleChange} className="w-full border border-slate-300 rounded p-2 focus:ring outline-none">
              <option value="not_allowed">Not Allowed</option>
              <option value="allowed_with_disclosure">Allowed with Disclosure</option>
              <option value="allowed">Allowed</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Feedback Mode</label>
            <select name="feedback_mode" value={formData.feedback_mode} onChange={handleChange} className="w-full border border-slate-300 rounded p-2 focus:ring outline-none">
              <option value="hints">Hints Only</option>
              <option value="full">Full Feedback</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Release Mode</label>
            <select name="release_mode" value={formData.release_mode} onChange={handleChange} className="w-full border border-slate-300 rounded p-2 focus:ring outline-none">
              <option value="after_approval">After Teacher Approval</option>
              <option value="auto">Automatic</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Paste Flag Threshold (chars)</label>
            <input type="number" required name="paste_flag_chars" value={formData.paste_flag_chars} onChange={handleChange} className="w-full border border-slate-300 rounded p-2 focus:ring outline-none" />
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="font-semibold text-lg border-b pb-2">Viva Configuration</h3>
          <div className="flex items-center gap-2">
            <input type="checkbox" name="viva_enabled" checked={formData.viva_enabled} onChange={handleChange} id="viva_enabled" className="w-4 h-4 text-blue-600" />
            <label htmlFor="viva_enabled" className="text-sm font-medium text-slate-700">Enable Viva Defense</label>
          </div>
          
          {formData.viva_enabled && (
            <div className="grid grid-cols-3 gap-4 p-4 bg-slate-50 rounded border border-slate-200">
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">Weight (0-1)</label>
                <input type="number" step="0.1" max="1" min="0" required name="viva_weight" value={formData.viva_weight} onChange={handleChange} className="w-full border border-slate-300 rounded p-1.5 focus:ring outline-none text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">Questions</label>
                <input type="number" required name="viva_question_count" value={formData.viva_question_count} onChange={handleChange} className="w-full border border-slate-300 rounded p-1.5 focus:ring outline-none text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">Time Limit (s)</label>
                <input type="number" required name="viva_time_limit_s" value={formData.viva_time_limit_s} onChange={handleChange} className="w-full border border-slate-300 rounded p-1.5 focus:ring outline-none text-sm" />
              </div>
            </div>
          )}
        </div>

        <div className="pt-4 border-t flex justify-end">
          <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded shadow transition-colors">
            Save Settings
          </button>
        </div>
      </form>

      {!isNew && (
        <div className="mt-8 space-y-8">
          <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
            <div className="flex justify-between items-center border-b pb-2 mb-4">
              <h3 className="font-semibold text-lg">Rubric</h3>
              <button 
                onClick={handleDraftRubric} 
                disabled={isDrafting}
                className="bg-indigo-100 hover:bg-indigo-200 text-indigo-700 px-3 py-1 rounded text-sm font-medium transition-colors disabled:opacity-50"
              >
                {isDrafting ? 'Drafting...' : '✨ Draft with AI'}
              </button>
            </div>
            
            {formData.rubric ? (
              <div className="space-y-4">
                {formData.rubric.criteria.map(c => (
                  <div key={c.id} className="p-4 bg-slate-50 border border-slate-200 rounded">
                    <h4 className="font-medium text-slate-800">{c.name} ({c.max_marks} marks, topic: {c.topic})</h4>
                    <p className="text-sm text-slate-600 mb-2">{c.description}</p>
                    <ol className="list-decimal pl-5 text-sm space-y-1 text-slate-700">
                      {c.levels.map((lvl, idx) => <li key={idx}>{lvl}</li>)}
                    </ol>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500">No rubric defined yet.</p>
            )}
          </div>

          <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
            <h3 className="font-semibold text-lg border-b pb-2 mb-4">Strictness Preview</h3>
            <p className="text-sm text-slate-600 mb-4">Test how the AI will grade a answer under different strictness policies.</p>
            <textarea 
              value={previewText}
              onChange={e => setPreviewText(e.target.value)}
              placeholder="Paste a student answer here..."
              className="w-full border rounded p-2 text-sm mb-4 h-32 focus:ring outline-none"
            />
            <button 
              onClick={handlePreviewStrictness}
              disabled={isPreviewing || !previewText}
              className="bg-indigo-100 hover:bg-indigo-200 text-indigo-700 px-4 py-2 rounded text-sm font-medium transition-colors disabled:opacity-50 mb-6"
            >
              {isPreviewing ? 'Evaluating...' : '✨ Preview Strictness'}
            </button>

            {strictnessPreview && (
              <div className="space-y-4">
                <p className="text-sm text-slate-500 italic">{strictnessPreview.note}</p>
                <div className="grid grid-cols-4 gap-4">
                  {strictnessPreview.levels.map(l => (
                    <div key={l.strictness} className={`p-4 rounded border ${l.strictness === formData.strictness ? 'border-indigo-400 bg-indigo-50 ring-1 ring-indigo-400' : 'border-slate-200 bg-slate-50'}`}>
                      <h4 className="font-semibold capitalize text-slate-800 mb-1">{l.strictness.replace('_', ' ')}</h4>
                      <div className="text-2xl font-bold text-slate-900">{l.total} <span className="text-sm font-normal text-slate-500">marks</span></div>
                      <div className="mt-2 space-y-1">
                        {l.criteria.map(c => (
                          <div key={c.criterion_id} className="flex justify-between text-xs text-slate-600">
                            <span>{c.criterion_id}</span>
                            <span>{c.marks}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
