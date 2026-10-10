import { Routes, Route, Link, useNavigate, useParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import type { Assessment } from '../../api/types';

export function TeacherApp() {
  return (
    <Routes>
      <Route path="/" element={<AssessmentList />} />
      <Route path="/assessments/new" element={<AssessmentSettings isNew />} />
      <Route path="/assessments/:id" element={<AssessmentDetail />} />
      <Route path="/assessments/:id/settings" element={<AssessmentSettings />} />
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
        <h2 className="text-3xl font-bold text-slate-800">Assessments</h2>
        <button 
          onClick={() => navigate('/teacher/assessments/new')}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded shadow transition-colors"
        >
          + New Assessment
        </button>
      </div>
      
      <div className="bg-white rounded-lg shadow border border-slate-200 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="p-4 text-sm font-semibold text-slate-600">Title</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Status</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Due</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Max Marks</th>
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
  const navigate = useNavigate();

  useEffect(() => {
    if (id) {
      apiClient<Assessment>(`/assessments/${id}`, { fixtureName: 'assessment_a1' })
        .then(setAssessment)
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
    </div>
  );
}
