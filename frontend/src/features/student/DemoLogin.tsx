import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import roster from '../../../../fixtures/demo/roster.json';

export function DemoLogin({ role }: { role: 'teacher' | 'student' }) {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  return <main className="student-page demo-login"><p className="eyebrow">VIVAGRADE</p>
    <h1>{role === 'teacher' ? 'Teacher' : 'Student'} sign in</h1>
    <p>Sign in to your classroom.</p>
    <form onSubmit={e => {
      e.preventDefault();
      const student = roster.find(row => row.reg_no === username.trim().toUpperCase());
      if (password !== 'Demo@123' || (role === 'teacher' ? username.trim() !== 'teacher' : !student)) {
        setError('Check your username and password.'); return;
      }
      localStorage.setItem('currentUserId', role === 'teacher' ? 'u_teacher_1' : student!.user_id);
      sessionStorage.setItem('vivagrade:demo-role', role);
      navigate(role === 'teacher' ? '/teacher/classroom' : '/student', { replace: true });
    }}>
      <label>{role === 'teacher' ? 'Username' : 'Registration number'}<input autoComplete="username" required value={username} onChange={e => setUsername(e.target.value)} /></label>
      <label>Password<input type="password" autoComplete="current-password" required value={password} onChange={e => setPassword(e.target.value)} /></label>
      {error && <p role="alert">{error}</p>}
      <button className="primary" type="submit">Sign in</button>
    </form>
    <p className="demo-note">Username: {role === 'teacher' ? 'teacher' : 'any listed registration number, e.g. FA23-BAI-045'}<br />Password: Demo@123</p>
    <Link to={role === 'teacher' ? '/login/student' : '/login/teacher'}>Sign in as {role === 'teacher' ? 'a student' : 'a teacher'}</Link>
  </main>;
}

export function DemoGuard({ role, children }: { role: 'teacher' | 'student'; children: React.ReactNode }) {
  return sessionStorage.getItem('vivagrade:demo-role') === role
    ? children : <Navigate to={`/login/${role}`} replace />;
}
