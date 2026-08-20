import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { TemplateLibrary } from './pages/TemplateLibrary';
import { ConversionWorkspace } from './pages/ConversionWorkspace';
import { UserManagement } from './pages/UserManagement';
import { AIConfig } from './pages/AIConfig';
import { ConversionHistory } from './pages/ConversionHistory';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/templates" element={<ProtectedRoute allowedRoles={['super_admin', 'admin']}><TemplateLibrary /></ProtectedRoute>} />
          <Route path="/convert" element={<ProtectedRoute allowedRoles={['super_admin', 'admin', 'recruiter']}><ConversionWorkspace /></ProtectedRoute>} />
          <Route path="/users" element={<ProtectedRoute allowedRoles={['super_admin', 'admin']}><UserManagement /></ProtectedRoute>} />
          <Route path="/ai-config" element={<ProtectedRoute allowedRoles={['super_admin']}><AIConfig /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><ConversionHistory /></ProtectedRoute>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
