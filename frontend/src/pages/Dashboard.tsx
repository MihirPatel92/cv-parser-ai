import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getStats } from '../api/admin';
import { getConversions } from '../api/conversions';
import { StatsCard } from '../components/StatsCard';
import { Badge } from '../components/Badge';
import { Users, FileText, Activity, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { format } from 'date-fns';

export const Dashboard: React.FC = () => {
  const { hasRole } = useAuth();
  const isAdmin = hasRole(['super_admin', 'admin']);

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
    enabled: isAdmin,
  });

  const { data: conversions, isLoading: convLoading } = useQuery({
    queryKey: ['conversions'],
    queryFn: getConversions,
    enabled: !isAdmin,
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <div className="space-x-3">
          {isAdmin && (
            <Link to="/templates" className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-50 transition-colors">
              Add Template
            </Link>
          )}
          <Link to="/convert" className="bg-primary-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-primary-700 transition-colors">
            Convert CV
          </Link>
        </div>
      </div>

      {isAdmin && stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatsCard title="Total Conversions" value={stats.total_conversions} icon={Activity} />
          <StatsCard title="Templates" value={stats.total_templates} icon={FileText} />
          <StatsCard title="Active Users" value={stats.total_users} icon={Users} />
          <StatsCard 
            title="Success Rate" 
            value={`${stats.total_conversions > 0 ? Math.round((stats.completed_conversions / stats.total_conversions) * 100) : 0}%`} 
            icon={CheckCircle2} 
          />
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">Recent Conversions</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-500">
            <thead className="text-xs text-gray-700 uppercase bg-gray-50">
              <tr>
                <th className="px-6 py-3">File</th>
                <th className="px-6 py-3">Template</th>
                {isAdmin && <th className="px-6 py-3">User</th>}
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Date</th>
              </tr>
            </thead>
            <tbody>
              {(isAdmin ? stats?.recent_conversions : conversions)?.slice(0, 5).map((conv) => (
                <tr key={conv.id} className="bg-white border-b hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900 truncate max-w-xs">{conv.source_cv_filename}</td>
                  <td className="px-6 py-4">{conv.template_name}</td>
                  {isAdmin && <td className="px-6 py-4">{conv.recruiter_name}</td>}
                  <td className="px-6 py-4">
                    <Badge status={conv.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {format(new Date(conv.created_at), 'MMM d, yyyy HH:mm')}
                  </td>
                </tr>
              ))}
              {(!isAdmin && conversions?.length === 0) || (isAdmin && stats?.recent_conversions.length === 0) ? (
                <tr>
                  <td colSpan={isAdmin ? 5 : 4} className="px-6 py-8 text-center text-gray-500">
                    No conversions found. Click "Convert CV" to start.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
