import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getConversions, downloadConversion } from '../api/conversions';
import { Badge } from '../components/Badge';
import { format } from 'date-fns';
import { FileDown, Search } from 'lucide-react';

export const ConversionHistory: React.FC = () => {
  const [filter, setFilter] = useState('all');
  const { data: conversions, isLoading } = useQuery({
    queryKey: ['conversions'],
    queryFn: getConversions
  });

  const filteredConversions = conversions?.filter(c => filter === 'all' || c.status === filter);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Conversion History</h1>
        <div className="flex items-center space-x-2 bg-white border rounded-lg px-3 py-2">
          <Search className="h-4 w-4 text-gray-400" />
          <select value={filter} onChange={e => setFilter(e.target.value)} className="border-none bg-transparent outline-none text-sm text-gray-700">
            <option value="all">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="pending">Pending</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-500">
            <thead className="text-xs text-gray-700 uppercase bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-4">Original File</th>
                <th className="px-6 py-4">Template</th>
                <th className="px-6 py-4">AI Engine</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Date</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredConversions?.map((conv) => (
                <tr key={conv.id} className="bg-white border-b hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 font-medium text-gray-900 truncate max-w-[200px]">{conv.source_cv_filename}</td>
                  <td className="px-6 py-4">{conv.template_name}</td>
                  <td className="px-6 py-4 capitalize">{conv.ai_provider}</td>
                  <td className="px-6 py-4"><Badge status={conv.status} /></td>
                  <td className="px-6 py-4 whitespace-nowrap">{format(new Date(conv.created_at), 'MMM d, yyyy HH:mm')}</td>
                  <td className="px-6 py-4 text-right">
                    {conv.status === 'completed' && (
                      <button 
                        onClick={() => downloadConversion(conv.id, conv.output_format === 'both' ? 'docx' : conv.output_format).then(blob => {
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement('a'); a.href = url; a.download = `cv.${conv.output_format === 'both' ? 'docx' : conv.output_format}`; a.click();
                        })}
                        className="inline-flex items-center text-primary-600 hover:text-primary-800 bg-primary-50 px-3 py-1.5 rounded-lg text-xs font-medium"
                      >
                        <FileDown className="h-4 w-4 mr-1" /> Download
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
