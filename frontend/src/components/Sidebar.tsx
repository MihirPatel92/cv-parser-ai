import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, FileText, FileUp, History, Users, Settings, LogOut } from 'lucide-react';
import { clsx } from 'clsx';

export const Sidebar: React.FC = () => {
  const { user, logout, hasRole } = useAuth();
  const location = useLocation();

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard, roles: ['super_admin', 'admin', 'recruiter'] },
    { name: 'Convert CV', path: '/convert', icon: FileUp, roles: ['super_admin', 'admin', 'recruiter'] },
    { name: 'Templates', path: '/templates', icon: FileText, roles: ['super_admin', 'admin'] },
    { name: 'History', path: '/history', icon: History, roles: ['super_admin', 'admin', 'recruiter'] },
    { name: 'Users', path: '/users', icon: Users, roles: ['super_admin', 'admin'] },
    { name: 'AI Config', path: '/ai-config', icon: Settings, roles: ['super_admin'] },
  ];

  const roleDisplay = user?.role ? String(user.role).replace('_', ' ') : 'User';

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col h-full">
      <div className="p-6">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-indigo-400 bg-clip-text text-transparent">
          CV Parser AI
        </h1>
      </div>
      
      <nav className="flex-1 px-4 space-y-1 mt-4">
        {navItems.filter(item => hasRole(item.roles)).map(item => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={clsx(
                'flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors',
                isActive
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              )}
            >
              <item.icon className={clsx('mr-3 h-5 w-5', isActive ? 'text-indigo-600' : 'text-gray-400')} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center px-4 py-3">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{user?.full_name || user?.email || 'Admin'}</p>
            <p className="text-xs text-gray-500 truncate capitalize">{roleDisplay}</p>
          </div>
          <button onClick={logout} title="Sign Out" className="text-gray-400 hover:text-gray-600 ml-2">
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
};
