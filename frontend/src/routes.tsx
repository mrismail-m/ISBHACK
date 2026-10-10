import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import type { User } from './api/types';
import { apiClient } from './api/client';

function RoleSwitcher() {
  const [users, setUsers] = useState<User[]>([]);
  const [currentUser, setCurrentUser] = useState<string | null>(localStorage.getItem('currentUserId'));

  useEffect(() => {
    apiClient<User[]>('/users', { fixtureName: 'users' }).then(data => {
      setUsers(data);
      if (!currentUser && data.length > 0) {
        handleUserSelect(data[0].id);
      }
    }).catch(console.error);
  }, [currentUser]);

  const handleUserSelect = (id: string) => {
    localStorage.setItem('currentUserId', id);
    setCurrentUser(id);
    window.location.reload();
  };

  const user = users.find(u => u.id === currentUser);

  return (
    <div className="bg-slate-900 text-white p-4 flex justify-between items-center shadow-md">
      <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">VivaGrade</h1>
      <div className="flex items-center gap-4">
        <span className="text-sm">Current: {user ? `${user.name} (${user.role})` : 'None'}</span>
        <select 
          className="bg-slate-800 border border-slate-700 p-2 rounded text-sm"
          value={currentUser || ''}
          onChange={(e) => handleUserSelect(e.target.value)}
        >
          {users.map(u => (
            <option key={u.id} value={u.id}>{u.name} ({u.role})</option>
          ))}
        </select>
        <div className="flex gap-4 text-sm font-medium">
          <Link to="/student" className="text-slate-300 hover:text-white transition-colors">Student</Link>
          <Link to="/teacher" className="text-slate-300 hover:text-white transition-colors">Teacher</Link>
        </div>
      </div>
    </div>
  );
}

function StudentApp() {
  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h2 className="text-3xl font-bold text-slate-800 mb-4">Student App</h2>
      <p className="text-slate-600">Skeleton for student interfaces (M0.2).</p>
    </div>
  );
}

function TeacherApp() {
  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h2 className="text-3xl font-bold text-slate-800 mb-4">Teacher Console</h2>
      <p className="text-slate-600">Skeleton for teacher interfaces (M0.2).</p>
    </div>
  );
}

export function AppRoutes() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50 font-sans">
        <RoleSwitcher />
        <Routes>
          <Route path="/" element={<Navigate to="/student" />} />
          <Route path="/student/*" element={<StudentApp />} />
          <Route path="/teacher/*" element={<TeacherApp />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
