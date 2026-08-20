import React from 'react';
import { clsx } from 'clsx';
import { ConversionStatus } from '../api/types';

export const Badge: React.FC<{ status: ConversionStatus | string }> = ({ status }) => {
  const colors = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  const colorClass = colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800';

  return (
    <span className={clsx('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize', colorClass)}>
      {status}
    </span>
  );
};
