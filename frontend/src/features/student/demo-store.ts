import type { ActivityBatch, ActivityEvents, Assessment, Submission, User } from '../../api/types';
export const demoUsers: User[] = [
  { id: 'u_teacher_1', name: 'Demo teacher', role: 'teacher', classroom_id: 'cl_1' },
  { id: 'u_student_3', name: 'Ayesha K.', role: 'student', classroom_id: 'cl_1' },
  { id: 'u_student_4', name: 'Hassan A.', role: 'student', classroom_id: 'cl_1' },
];
const demoAssessment: Assessment = {
  id: 'a_1', classroom_id: 'cl_1', kind: 'assignment', title: 'Hash table collisions',
  instructions_md: '# Explain hash table collisions\n\nIn about 300 words, explain why collisions happen and compare **chaining** with **open addressing**. Include an example and discuss average and worst-case lookup complexity.',
  max_marks: 20, pass_mark_pct: 50, rubric: { criteria: ['Concept accuracy', 'Strategies', 'Complexity', 'Communication'].map((name, i) => ({ id: `c${i + 1}`, name, description: name, max_marks: 5, topic: ['hashing', 'collisions', 'complexity', 'communication'][i], levels: ['Absent', 'Minimal', 'Partial', 'Mostly correct', 'Complete'] })) },
  model_answer_md: null, strictness: 'normal', viva_enabled: true, viva_weight: 0.3, viva_question_count: 3,
  viva_time_limit_s: 90, feedback_mode: 'full', release_mode: 'after_approval', ai_policy: 'allowed_with_disclosure',
  paste_flag_chars: 500, topics: ['hashing', 'collisions', 'complexity'], status: 'open',
  due_at: '2026-10-12T18:00:00Z', created_at: '2026-10-10T05:00:00Z',
};
function read<T>(key: string, fallback: T): T {
  try { return JSON.parse(localStorage.getItem(key) || 'null') as T || fallback; } catch { return fallback; }
}
const store = (key: string, value: unknown) => localStorage.setItem(key, JSON.stringify(value));
const submissionKey = (id: string) => `vivagrade:demo:submission:${id}`;
// Browser-only fallback until endpoint owners provide their fixtures. Never used in real mode.
export function demoRequest(endpoint: string, options: RequestInit): unknown {
  const path = endpoint.split('?')[0];
  const method = options.method || 'GET';
  if (path === '/submissions/s_result_demo/result') return {
    submission_id: 's_result_demo', assessment_id: 'a_1', max_marks: 20, work_marks: 15.5,
    understanding: 0.72, viva_weight: 0.3, final_marks: 15.2, grace_marks: 2,
    final_with_grace: 17.2, final_pct: 86, released_at: '2026-10-10T09:00:00Z',
    feedback: { mode: 'full', strengths: [{ criterion_id: 'c1', text: 'You defined collisions clearly and used a useful example.', quote: 'two keys map to the same index' }],
      improvements: [{ criterion_id: 'c3', text: 'Compare average and worst-case lookup time.', quote: 'lookups are fast', hint: 'What happens when the table is almost full?', explanation: 'Longer chains or probe sequences can make a lookup approach O(n) in the worst case.' }],
      next_step: 'Rewrite the complexity paragraph to compare both strategies.', topics: [{ tag: 'hashing', level: 'strong' }, { tag: 'complexity', level: 'weak' }] },
  };
  if (path === '/users') return demoUsers;
  if (path === '/assessments' && method === 'GET') return [demoAssessment];
  if (path === '/assessments/a_1' && method === 'GET') return demoAssessment;
  if (path === '/assessments/a_1/submissions' && method === 'POST') {
    const student_id = localStorage.getItem('currentUserId') || 'u_student_3';
    const submissionId = `s_demo_${student_id}`;
    const submission = read<Submission>(submissionKey(submissionId), { id: submissionId, assessment_id: 'a_1', student_id, content_md: '', answers: [], status: 'draft', started_at: new Date().toISOString(), submitted_at: null });
    store(submissionKey(submissionId), submission);
    return submission;
  }
  const match = /^\/submissions\/([^/]+)(.*)$/.exec(path);
  if (match) {
    const [, submissionId, suffix] = match;
    const submission = read<Submission | null>(submissionKey(submissionId), null);
    if (!submission) throw new Error('Demo submission not found. Open the assessment first.');
    if (suffix === '/result') throw Object.assign(new Error('Your teacher has not released your result yet.'), { code: 'not_released' });
    if (suffix === '/activity' && method === 'POST') {
      const batch = JSON.parse(String(options.body)) as ActivityBatch;
      const key = `vivagrade:demo:activity:${submissionId}`;
      const data = read<ActivityEvents>(key, { sessions: [], events: [] });
      if (!data.sessions.some(s => s.session_id === batch.session_id)) data.sessions.push({ session_id: batch.session_id, started_at: batch.session_started_at });
      const last = Math.max(-1, ...data.events.filter(e => e.session_id === batch.session_id).map(e => e.seq));
      const fresh = batch.events.filter(e => e.seq > last);
      data.events.push(...fresh.map(e => ({ ...e, session_id: batch.session_id })));
      store(key, data);
      return { received: fresh.length, last_seq: Math.max(last, ...fresh.map(e => e.seq)) };
    }
    if (suffix === '/activity/events') return read<ActivityEvents>(`vivagrade:demo:activity:${submissionId}`, { sessions: [], events: [] });
    if (!suffix && method === 'GET') return submission;
    if ((!suffix && method === 'PUT') || (suffix === '/submit' && method === 'POST')) {
      if (submission.status !== 'draft') throw new Error('This submission is already submitted.');
      if (method === 'PUT') submission.content_md = (JSON.parse(String(options.body)) as { content_md: string }).content_md;
      else { submission.status = 'submitted'; submission.submitted_at = new Date().toISOString(); }
      store(submissionKey(submissionId), submission);
      return submission;
    }
  }
  throw new Error(`Demo fixture is not available for ${method} ${path}.`);
}
