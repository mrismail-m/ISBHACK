import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { useNavigate } from 'react-router-dom';
import { DemoLogin, DemoGuard } from './features/student/DemoLogin';
import roster from '../../fixtures/demo/roster.json';
import './features/student/student.css';
const AssessmentEditor = lazy(() => import('./features/student/StudentApp').then(m => ({ default: m.AssessmentEditor })));
const AssessmentList = lazy(() => import('./features/student/StudentApp').then(m => ({ default: m.AssessmentList })));
const StudentResultPage = lazy(() => import('./features/student/StudentResult').then(m => ({ default: m.StudentResultPage })));
const StudentVivaPage = lazy(() => import('./features/student/StudentViva').then(m => ({ default: m.StudentVivaPage })));
const TeacherApp = lazy(() => import('./features/teacher/TeacherApp').then(m => ({ default: m.TeacherApp })));
function DemoHeader() {
  const navigate = useNavigate();
  const role = sessionStorage.getItem('vivagrade:demo-role');
  const student = roster.find(row => row.user_id === localStorage.getItem('currentUserId'));
  return <header className="app-nav"><Link className="wordmark" to={role === 'teacher' ? '/teacher/classroom' : '/student'}>VivaGrade<span>Grade the work. Verify the learning.</span></Link><nav>
    {role ? <><span>{role === 'teacher' ? 'Teacher' : `${student?.name || 'Student'} · ${student?.reg_no || ''}`}</span><button onClick={() => { sessionStorage.removeItem('vivagrade:demo-role'); localStorage.removeItem('currentUserId'); navigate(`/login/${role}`); }}>Sign out</button></> : <><Link to="/login/student">Student login</Link><Link to="/login/teacher">Teacher login</Link></>}
  </nav></header>;
}
export function AppRoutes() {
  return <BrowserRouter><DemoHeader /><Suspense fallback={<main className="student-page" role="status">Opening your page...</main>}><Routes>
    <Route path="/" element={<Navigate to="/login/student" replace />} />
    <Route path="/login/student" element={<DemoLogin key="student" role="student" />} />
    <Route path="/login/teacher" element={<DemoLogin key="teacher" role="teacher" />} />
    <Route path="/student" element={<DemoGuard role="student"><AssessmentList /></DemoGuard>} />
    <Route path="/student/assessments/:assessmentId" element={<DemoGuard role="student"><AssessmentEditor /></DemoGuard>} />
    <Route path="/student/submissions/:submissionId/result" element={<DemoGuard role="student"><StudentResultPage /></DemoGuard>} />
    <Route path="/student/submissions/:submissionId/viva" element={<DemoGuard role="student"><StudentVivaPage /></DemoGuard>} />
    <Route path="/teacher/*" element={<DemoGuard role="teacher"><TeacherApp /></DemoGuard>} />
    <Route path="*" element={<main className="student-page"><h1>Page not found</h1><Link to="/student">Back to assessments</Link></main>} />
  </Routes></Suspense></BrowserRouter>;
}
