import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import type { User } from './api/types';
import { studentApi } from './api/student';
import { AssessmentEditor, AssessmentList } from './features/student/StudentApp';
import { StudentResultPage } from './features/student/StudentResult';
import { StudentVivaPage } from './features/student/StudentViva';
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
import { TeacherApp } from './features/teacher/TeacherApp';
export function AppRoutes() {
  return <BrowserRouter><RoleSwitcher /><Routes>
    <Route path="/" element={<Navigate to="/student" replace />} />
    <Route path="/student" element={<AssessmentList />} />
    <Route path="/student/assessments/:assessmentId" element={<AssessmentEditor />} />
    <Route path="/student/submissions/:submissionId/result" element={<StudentResultPage />} />
    <Route path="/student/submissions/:submissionId/viva" element={<StudentVivaPage />} />
    <Route path="/teacher/*" element={<TeacherApp />} />
    <Route path="*" element={<main className="student-page"><h1>Page not found</h1><Link to="/student">Back to assessments</Link></main>} />
  </Routes></BrowserRouter>;
}
