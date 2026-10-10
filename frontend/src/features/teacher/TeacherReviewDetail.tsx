import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { apiClient } from '../../api/client';
import type { Submission, Grade, ApproveRequest, Assessment } from '../../api/types';
import { ActivityInsights } from '../insights/ActivityInsights';

export function TeacherReviewDetail() {
  const { submissionId } = useParams<{ submissionId: string }>();
  const navigate = useNavigate();
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [grade, setGrade] = useState<Grade | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  
  const [overrides, setOverrides] = useState<Record<string, { marks: number, note: string }>>({});
  const [teacherNote, setTeacherNote] = useState('');
  const [feedbackEdits] = useState<Record<string, string>>({});

  useEffect(() => {
    if (submissionId) {
      apiClient<Submission>(`/submissions/${submissionId}`)
        .then(sub => {
          setSubmission(sub);
          return apiClient<Assessment>(`/assessments/${sub.assessment_id}`);
        })
        .then(setAssessment)
        .catch(console.error);

      apiClient<Grade>(`/submissions/${submissionId}/grade`)
        .then(setGrade)
        .catch(console.error);
    }
  }, [submissionId]);

  if (!submission || !grade || !assessment) return <div className="p-8 text-center">Loading...</div>;

  const handleOverrideChange = (criterionId: string, marks: number, note: string) => {
    setOverrides(prev => ({
      ...prev,
      [criterionId]: { marks, note }
    }));
  };

  const handleApprove = async (release: boolean) => {
    try {
      const payload: ApproveRequest = {
        criteria_overrides: Object.entries(overrides).map(([id, o]) => ({ criterion_id: id, marks: o.marks, note: o.note })),
        teacher_note: teacherNote || null,
        feedback_edits: feedbackEdits,
        release
      };
      await apiClient(`/submissions/${submissionId}/approve`, {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      navigate(`/teacher/assessments/${assessment.id}`);
    } catch (err) {
      console.error(err);
      alert('Failed to approve');
    }
  };

  const currentFinalTotal = grade.criteria.reduce((sum, c) => {
    const o = overrides[c.criterion_id];
    return sum + (o ? o.marks : c.final_marks);
  }, 0);

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <div>
        <Link to={`/teacher/assessments/${assessment.id}`} className="text-blue-600 hover:underline mb-4 inline-block">&larr; Back to Queue</Link>
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-slate-800">Review Submission</h2>
            <p className="text-slate-600">Total Marks: {currentFinalTotal} / {assessment.max_marks}</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => handleApprove(false)} className="bg-slate-200 hover:bg-slate-300 text-slate-800 px-4 py-2 rounded shadow transition-colors">
              Approve
            </button>
            <button onClick={() => handleApprove(true)} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded shadow transition-colors">
              Approve & Release
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-8">
        <div className="col-span-2 space-y-6">
          <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
            <h3 className="font-semibold text-lg border-b pb-2 mb-4">Submission Content</h3>
            <div className="prose prose-slate max-w-none whitespace-pre-wrap">
              {submission.content_md}
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
            <h3 className="font-semibold text-lg border-b pb-2 mb-4">AI Grading Draft</h3>
            <div className="space-y-6">
              {grade.criteria.map(c => {
                const override = overrides[c.criterion_id];
                return (
                  <div key={c.criterion_id} className="p-4 bg-slate-50 border border-slate-200 rounded">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-medium">{c.criterion_id}</h4>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-slate-500">AI: {c.ai_marks}</span>
                        <input 
                          type="number" 
                          step="0.5" 
                          min="0"
                          max={assessment.max_marks} // Should be criterion max_marks, but we don't have it here easily
                          value={override ? override.marks : c.final_marks}
                          onChange={e => handleOverrideChange(c.criterion_id, Number(e.target.value), override?.note || c.teacher_note || '')}
                          className="w-16 border rounded p-1 text-sm text-center"
                        />
                      </div>
                    </div>
                    {c.evidence.map((e, idx) => (
                      <blockquote key={idx} className="border-l-4 border-blue-300 pl-3 my-2 text-sm text-slate-600 italic">
                        "{e.quote}" {e.verified ? '✓' : '⚠️'}
                      </blockquote>
                    ))}
                    <p className="text-sm text-slate-700 mt-2">{c.reasoning}</p>
                    
                    <div className="mt-3">
                      <input 
                        type="text" 
                        placeholder="Teacher note for this criterion (optional)" 
                        value={override ? override.note : c.teacher_note || ''}
                        onChange={e => handleOverrideChange(c.criterion_id, override ? override.marks : c.final_marks, e.target.value)}
                        className="w-full text-sm border border-slate-300 rounded p-1.5"
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
            <h3 className="font-semibold text-lg border-b pb-2 mb-4">Overall Feedback</h3>
            <textarea
              className="w-full border rounded p-2 text-sm min-h-[100px]"
              placeholder="Add an overall note to the student..."
              value={teacherNote}
              onChange={e => setTeacherNote(e.target.value)}
            />
          </div>

          <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
            <h3 className="font-semibold text-lg border-b pb-2 mb-4">Flags</h3>
            <div className="flex flex-wrap gap-2">
              {grade.grader_flags.map(f => (
                <span key={f} className="bg-red-100 text-red-700 px-2 py-1 rounded text-xs capitalize">
                  {f.replace('_', ' ')}
                </span>
              ))}
              {grade.grader_flags.length === 0 && <span className="text-slate-500 text-sm">No flags</span>}
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
             {submissionId && <ActivityInsights submissionId={submissionId} />}
          </div>
        </div>
      </div>
    </div>
  );
}
