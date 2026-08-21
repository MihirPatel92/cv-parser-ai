import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getTemplates } from '../api/templates';
import { createConversion, getConversion, downloadConversion } from '../api/conversions';
import { getAIConfig } from '../api/admin';
import { FileUpload } from '../components/FileUpload';
import { Badge } from '../components/Badge';
import { FileDown, Loader2, ArrowRight, AlertCircle, CheckCircle2 } from 'lucide-react';
import toast from 'react-hot-toast';

export const ConversionWorkspace: React.FC = () => {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [templateId, setTemplateId] = useState('');
  const [aiProvider, setAiProvider] = useState<'gemini' | 'openai' | 'ollama'>('gemini');
  const [outputFormat, setOutputFormat] = useState('docx');
  const [activeConversionId, setActiveConversionId] = useState<string | null>(null);

  const { data: templates, isLoading: templatesLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: getTemplates,
  });

  const { data: aiConfig } = useQuery({
    queryKey: ['aiConfig'],
    queryFn: getAIConfig,
  });

  const { data: conversion, refetch: refetchConversion } = useQuery({
    queryKey: ['conversion', activeConversionId],
    queryFn: () => getConversion(activeConversionId!),
    enabled: !!activeConversionId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'pending' || status === 'processing' ? 2500 : false;
    },
  });

  React.useEffect(() => {
    if (aiConfig?.provider) {
      setAiProvider(aiConfig.provider as any);
    }
  }, [aiConfig]);

  const convertMutation = useMutation({
    mutationFn: createConversion,
    onSuccess: (data) => {
      setActiveConversionId(data.id);
      queryClient.invalidateQueries({ queryKey: ['conversions'] });
      toast.success('Conversion started! Processing CV with AI...');
    },
    onError: (err: any) => {
      console.error('Conversion submission error:', err);
      const detail = err.response?.data?.detail || 'Failed to start conversion';
      toast.error(detail);
    },
  });

  const handleConvert = () => {
    if (!file) return toast.error('Please upload a source CV (PDF or DOCX)');
    if (!templateId) return toast.error('Please select a target company template');

    const formData = new FormData();
    formData.append('file', file);
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
      a.download = `formatted_cv.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success(`Downloaded ${format.toUpperCase()}`);
    } catch (e) {
      console.error('Download failed:', e);
      toast.error(`Download failed for ${format.toUpperCase()}`);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Transform & Format CV</h1>
        <p className="text-sm text-gray-500 mt-1">
          Upload a candidate CV and select a company template to automatically extract, re-sequence, and format candidate details.
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-8">
        {/* Step 1 */}
        <div>
          <h2 className="text-base font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 text-xs font-bold">1</span>
            Upload Source Candidate CV
          </h2>
          <FileUpload
            accept={{
              'application/pdf': ['.pdf'],
              'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            }}
            onDrop={(files) => setFile(files[0])}
            file={file}
            label="Drop candidate CV (PDF / DOCX) here"
          />
        </div>

        {/* Step 2 & 3 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h2 className="text-base font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 text-xs font-bold">2</span>
              Select Target Template
            </h2>
            <select
              value={templateId}
              onChange={(e) => setTemplateId(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 bg-white focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
            >
              <option value="">-- Choose a company template --</option>
              {templates?.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} {t.company_name ? `(${t.company_name})` : ''} [{t.file_type.toUpperCase()}]
                </option>
              ))}
            </select>
            {templates?.length === 0 && !templatesLoading && (
              <p className="text-xs text-amber-600 mt-1.5">
                No templates found. Please upload a template in the Template Library first.
              </p>
            )}
          </div>

          <div>
            <h2 className="text-base font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 text-xs font-bold">3</span>
              AI Engine & Provider
            </h2>
            <select
              value={aiProvider}
              onChange={(e) => setAiProvider(e.target.value as any)}
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 bg-white focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
            >
              <option value="gemini">Google Gemini (Recommended - 1.5 Flash)</option>
              <option value="openai">OpenAI (GPT-4o Mini)</option>
              <option value="ollama">Local Ollama (DeepSeek / LLaMA)</option>
            </select>
          </div>
        </div>

        {/* Step 4 */}
        <div>
          <h2 className="text-base font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 text-xs font-bold">4</span>
            Desired Output Format
          </h2>
          <div className="flex gap-6">
            {[
              { id: 'docx', label: 'DOCX (Word Document)' },
              { id: 'pdf', label: 'PDF (Print Ready)' },
              { id: 'both', label: 'Both (DOCX + PDF)' },
            ].map((fmt) => (
              <label key={fmt.id} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  name="output_format"
                  value={fmt.id}
                  checked={outputFormat === fmt.id}
                  onChange={(e) => setOutputFormat(e.target.value)}
                  className="text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                />
                <span className="text-sm font-medium text-gray-700">{fmt.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="pt-4 border-t border-gray-100 flex justify-end">
          <button
            onClick={handleConvert}
            disabled={!file || !templateId || convertMutation.isPending}
            className="flex items-center px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 focus:ring-4 focus:ring-indigo-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          >
            {convertMutation.isPending ? (
              <>
                <Loader2 className="animate-spin h-5 w-5 mr-2" />
                Starting Conversion...
              </>
            ) : (
              <>
                <ArrowRight className="h-5 w-5 mr-2" />
                Start AI Conversion
              </>
            )}
          </button>
        </div>
      </div>

      {/* Real-time Status Card */}
      {conversion && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
          <h2 className="text-base font-semibold text-gray-900">Conversion Status</h2>

          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <p className="font-medium text-gray-900">{conversion.source_cv_filename}</p>
              <p className="text-xs text-gray-500 mt-0.5">
                Target Template: <span className="font-medium">{conversion.template_name || 'Standard'}</span> • Provider: <span className="capitalize">{conversion.ai_provider}</span>
              </p>
              {conversion.processing_time_seconds && (
                <p className="text-xs text-gray-400 mt-0.5">
                  Processed in {conversion.processing_time_seconds}s
                </p>
              )}
            </div>

            <div className="flex items-center gap-3">
              <Badge status={conversion.status} />

              {(conversion.status === 'pending' || conversion.status === 'processing') && (
                <div className="flex items-center text-xs text-indigo-600 font-medium animate-pulse">
                  <Loader2 className="animate-spin h-4 w-4 mr-1" />
                  AI parsing in progress...
                </div>
              )}

              {conversion.status === 'completed' && (
                <div className="flex gap-2">
                  {(conversion.output_format === 'docx' || conversion.output_format === 'both' || conversion.has_docx) && (
                    <button
                      onClick={() => handleDownload('docx')}
                      className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-md hover:bg-indigo-100 transition-colors"
                    >
                      <FileDown className="h-4 w-4 mr-1" /> Download DOCX
                    </button>
                  )}
                  {(conversion.output_format === 'pdf' || conversion.output_format === 'both' || conversion.has_pdf) && (
                    <button
                      onClick={() => handleDownload('pdf')}
                      className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-red-700 bg-red-50 border border-red-200 rounded-md hover:bg-red-100 transition-colors"
                    >
                      <FileDown className="h-4 w-4 mr-1" /> Download PDF
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>

          {conversion.status === 'failed' && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3 text-red-700 text-sm">
              <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5 text-red-500" />
              <div>
                <p className="font-medium">Conversion Failed</p>
                <p className="text-xs text-red-600 mt-1">
                  {conversion.error_message || 'An unexpected error occurred during AI processing.'}
                </p>
                <p className="text-xs text-red-500 mt-2">
                  Tip: Ensure your Gemini API Key is configured under <strong>AI Config</strong> and that the target template is valid.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
