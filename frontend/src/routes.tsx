import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom';
import { useState, useEffect, lazy, Suspense } from 'react';
import type { User } from './api/types';
import { studentApi } from './api/student';
import './features/student/student.css';
const AssessmentEditor = lazy(() => import('./features/student/StudentApp').then(m => ({ default: m.AssessmentEditor })));
const AssessmentList = lazy(() => import('./features/student/StudentApp').then(m => ({ default: m.AssessmentList })));
const StudentResultPage = lazy(() => import('./features/student/StudentResult').then(m => ({ default: m.StudentResultPage })));
const StudentVivaPage = lazy(() => import('./features/student/StudentViva').then(m => ({ default: m.StudentVivaPage })));
const TeacherApp = lazy(() => import('./features/teacher/TeacherApp').then(m => ({ default: m.TeacherApp })));
function RoleSwitcher() {
  const [users, setUsers] = useState<User[]>([]);
  const [currentUser, setCurrentUser] = useState(localStorage.getItem('currentUserId') || '');
  const [error, setError] = useState('');
  useEffect(() => {
    studentApi.users().then(data => {
      setUsers(data);
      if (!data.some(u => u.id === localStorage.getItem('currentUserId'))) {
        const selected = data.find(u => u.role === 'student') || data[0];
        if (selected) { localStorage.setItem('currentUserId', selected.id); setCurrentUser(selected.id); }
      }
    }).catch(e => setError(e.message));
  }, []);
  return <header className="app-nav"><Link className="wordmark" to="/student">VivaGrade<span>Grade the work. Verify the learning.</span></Link><nav><Link to="/student">Student</Link><Link to="/teacher">Teacher</Link><label>Viewing as <select aria-label="Choose seeded user" value={currentUser} onChange={e => { localStorage.setItem('currentUserId', e.target.value); window.location.reload(); }}>{users.map(u => <option key={u.id} value={u.id}>{u.name} ({u.role})</option>)}</select></label>{error && <span role="alert">{error}</span>}</nav></header>;
}
export function AppRoutes() {
  return <BrowserRouter><RoleSwitcher /><Suspense fallback={<main className="student-page" role="status">Opening your page...</main>}><Routes>
    <Route path="/" element={<Navigate to="/student" replace />} />
    <Route path="/student" element={<AssessmentList />} />
    <Route path="/student/assessments/:assessmentId" element={<AssessmentEditor />} />
    <Route path="/student/submissions/:submissionId/result" element={<StudentResultPage />} />
    <Route path="/student/submissions/:submissionId/viva" element={<StudentVivaPage />} />
    <Route path="/teacher/*" element={<TeacherApp />} />
    <Route path="*" element={<main className="student-page"><h1>Page not found</h1><Link to="/student">Back to assessments</Link></main>} />
  </Routes></Suspense></BrowserRouter>;
}
