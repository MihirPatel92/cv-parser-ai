import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getTemplates, uploadTemplate, deleteTemplate, getTemplatePlaceholders } from '../api/templates';
import { FileUpload } from '../components/FileUpload';
import { Plus, Trash2, Eye } from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

export const TemplateLibrary: React.FC = () => {
  const queryClient = useQueryClient();
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showPlaceholdersModal, setShowPlaceholdersModal] = useState<string | null>(null);
  
  // Form state
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [description, setDescription] = useState('');

  const { data: templates, isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: getTemplates,
  });

  const { data: placeholders } = useQuery({
    queryKey: ['template-placeholders', showPlaceholdersModal],
    queryFn: () => getTemplatePlaceholders(showPlaceholdersModal!),
    enabled: !!showPlaceholdersModal,
  });

  const uploadMutation = useMutation({
    mutationFn: uploadTemplate,
    onSuccess: () => {
      toast.success('Template uploaded successfully');
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setShowUploadModal(false);
      setFile(null);
      setName('');
      setCompanyName('');
      setDescription('');
    },
    onError: () => toast.error('Failed to upload template'),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteTemplate,
    onSuccess: () => {
      toast.success('Template deleted');
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });

  const handleUploadSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return toast.error('Please select a file');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    formData.append('company_name', companyName);
    formData.append('description', description);
    
    uploadMutation.mutate(formData);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Template Library</h1>
        <button
          onClick={() => setShowUploadModal(true)}
          className="flex items-center bg-primary-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-primary-700 transition-colors"
        >
          <Plus className="h-4 w-4 mr-2" />
          Upload Template
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates?.map((template) => (
          <div key={template.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="font-semibold text-gray-900 text-lg">{template.name}</h3>
                <p className="text-sm text-primary-600 font-medium">{template.company_name}</p>
              </div>
              <span className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded uppercase font-medium">
                {template.file_type}
              </span>
            </div>
            <p className="text-sm text-gray-500 mb-6 flex-1">{template.description}</p>
            <div className="flex items-center justify-between text-xs text-gray-400 mb-4 border-t pt-4">
              <span>By {template.uploaded_by_name}</span>
              <span>{format(new Date(template.created_at), 'MMM d, yyyy')}</span>
            </div>
            <div className="flex gap-2">
              <button 
                onClick={() => setShowPlaceholdersModal(template.id)}
                className="flex-1 flex justify-center items-center py-2 px-3 bg-primary-50 text-primary-700 rounded-lg hover:bg-primary-100 transition-colors text-sm font-medium"
              >
                <Eye className="h-4 w-4 mr-1" /> View Tags
              </button>
              <button 
                onClick={() => {
                  if (confirm('Are you sure you want to delete this template?')) {
                    deleteMutation.mutate(template.id);
                  }
                }}
                className="p-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
        {templates?.length === 0 && (
          <div className="col-span-full bg-white p-12 text-center rounded-xl border border-gray-200 border-dashed">
            <p className="text-gray-500">No templates found. Upload one to get started.</p>
          </div>
        )}
      </div>

      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold mb-4">Upload New Template</h2>
            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <FileUpload
                accept={{ 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] }}
                onDrop={(files) => setFile(files[0])}
                file={file}
                label="Drop DOCX or PDF template here"
              />
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Template Name</label>
                <input required type="text" value={name} onChange={e => setName(e.target.value)} className="w-full border px-3 py-2 rounded-lg" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Company Name</label>
                <input required type="text" value={companyName} onChange={e => setCompanyName(e.target.value)} className="w-full border px-3 py-2 rounded-lg" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea rows={3} value={description} onChange={e => setDescription(e.target.value)} className="w-full border px-3 py-2 rounded-lg"></textarea>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button type="button" onClick={() => setShowUploadModal(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
                <button type="submit" disabled={uploadMutation.isPending} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                  {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showPlaceholdersModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 max-h-[80vh] flex flex-col">
            <h2 className="text-xl font-bold mb-4">Detected Placeholders</h2>
            <div className="flex-1 overflow-y-auto mb-4 border rounded-lg p-4 bg-gray-50">
              {placeholders?.length ? (
                <div className="flex flex-wrap gap-2">
                  {placeholders.map(p => (
                    <span key={p} className="bg-blue-100 text-blue-800 font-mono text-sm px-2 py-1 rounded">
                      {p}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">No placeholders found or loading...</p>
              )}
            </div>
            <div className="flex justify-end">
              <button onClick={() => setShowPlaceholdersModal(null)} className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
