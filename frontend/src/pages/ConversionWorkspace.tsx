import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getTemplates } from '../api/templates';
import { createConversion, getConversion, downloadConversion } from '../api/conversions';
import { getAIConfig } from '../api/admin';
import { FileUpload } from '../components/FileUpload';
import { Badge } from '../components/Badge';
import { FileDown, Loader2, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';

export const ConversionWorkspace: React.FC = () => {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [templateId, setTemplateId] = useState('');
  const [aiProvider, setAiProvider] = useState<'gemini' | 'openai' | 'ollama'>('gemini');
  const [outputFormat, setOutputFormat] = useState('docx');
  const [activeConversionId, setActiveConversionId] = useState<string | null>(null);

  const { data: templates } = useQuery({ queryKey: ['templates'], queryFn: getTemplates });
  const { data: aiConfig } = useQuery({ queryKey: ['aiConfig'], queryFn: getAIConfig });

  const { data: conversion, refetch: refetchConversion } = useQuery({
    queryKey: ['conversion', activeConversionId],
    queryFn: () => getConversion(activeConversionId!),
    enabled: !!activeConversionId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'pending' || status === 'processing' ? 3000 : false;
    }
  });

  React.useEffect(() => {
    if (aiConfig) {
      setAiProvider(aiConfig.provider);
    }
  }, [aiConfig]);

  const convertMutation = useMutation({
    mutationFn: createConversion,
    onSuccess: (data) => {
      setActiveConversionId(data.id);
      toast.success('Conversion started');
    },
    onError: () => toast.error('Failed to start conversion')
  });

  const handleConvert = () => {
    if (!file || !templateId) return toast.error('File and template are required');
    const formData = new FormData();
    formData.append('cv_file', file);
    formData.append('template_id', templateId);
    formData.append('ai_provider', aiProvider);
    formData.append('output_format', outputFormat);
    convertMutation.mutate(formData);
  };

  const handleDownload = async (format: string) => {
    if (!activeConversionId) return;
    try {
      const blob = await downloadConversion(activeConversionId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `converted_cv.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      toast.error('Download failed');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Convert CV</h1>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-8">
        <div>
          <h2 className="text-lg font-medium text-gray-900 mb-4">1. Upload Source CV</h2>
          <FileUpload
            accept={{ 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] }}
            onDrop={(files) => setFile(files[0])}
            file={file}
            label="Drop CV (PDF/DOCX) here"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h2 className="text-lg font-medium text-gray-900 mb-4">2. Select Template</h2>
            <select
              value={templateId}
              onChange={e => setTemplateId(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 bg-white focus:ring-2 focus:ring-primary-500 outline-none"
            >
              <option value="">-- Choose a template --</option>
              {templates?.map(t => (
                <option key={t.id} value={t.id}>{t.name} ({t.company_name})</option>
              ))}
            </select>
          </div>

          <div>
            <h2 className="text-lg font-medium text-gray-900 mb-4">3. AI Provider</h2>
            <select
              value={aiProvider}
              onChange={e => setAiProvider(e.target.value as any)}
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 bg-white focus:ring-2 focus:ring-primary-500 outline-none"
            >
              <option value="gemini">Google Gemini</option>
              <option value="openai">OpenAI</option>
              <option value="ollama">Local Ollama</option>
            </select>
          </div>
        </div>

        <div>
          <h2 className="text-lg font-medium text-gray-900 mb-4">4. Output Format</h2>
          <div className="flex gap-4">
            {['docx', 'pdf', 'both'].map(fmt => (
              <label key={fmt} className="flex items-center space-x-2">
                <input
                  type="radio"
                  name="format"
                  value={fmt}
                  checked={outputFormat === fmt}
                  onChange={e => setOutputFormat(e.target.value)}
                  className="text-primary-600 focus:ring-primary-500 h-4 w-4"
                />
                <span className="uppercase text-sm font-medium text-gray-700">{fmt}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="pt-4 border-t border-gray-100 flex justify-end">
          <button
            onClick={handleConvert}
            disabled={!file || !templateId || convertMutation.isPending}
            className="flex items-center px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50"
          >
            {convertMutation.isPending ? <Loader2 className="animate-spin h-5 w-5 mr-2" /> : <ArrowRight className="h-5 w-5 mr-2" />}
            Start Conversion
          </button>
        </div>
      </div>

      {conversion && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Conversion Result</h2>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border">
            <div>
              <p className="font-medium text-gray-900">{conversion.source_cv_filename}</p>
              <p className="text-sm text-gray-500">Template: {conversion.template_name}</p>
            </div>
            <div className="flex items-center gap-4">
              <Badge status={conversion.status} />
              
              {conversion.status === 'completed' && (
                <div className="flex gap-2">
                  {(conversion.output_format === 'docx' || conversion.output_format === 'both') && (
                    <button onClick={() => handleDownload('docx')} className="p-2 text-primary-600 hover:bg-primary-50 rounded bg-white border">
                      <FileDown className="h-5 w-5" /> DOCX
                    </button>
                  )}
                  {(conversion.output_format === 'pdf' || conversion.output_format === 'both') && (
                    <button onClick={() => handleDownload('pdf')} className="p-2 text-red-600 hover:bg-red-50 rounded bg-white border">
                      <FileDown className="h-5 w-5" /> PDF
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
