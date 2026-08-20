import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAIConfig, updateAIConfig } from '../api/admin';
import { AIConfig as AIConfigType, AIProvider } from '../api/types';
import toast from 'react-hot-toast';
import { Bot, Key, Server, Sliders, CheckCircle, ChevronDown } from 'lucide-react';

const PROVIDERS: { value: AIProvider; label: string; description: string; models: string[] }[] = [
  {
    value: 'gemini',
    label: 'Google Gemini',
    description: 'Google\'s multimodal AI. Great for structured extraction. Free tier available.',
    models: ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash', 'gemini-2.5-pro'],
  },
  {
    value: 'openai',
    label: 'OpenAI GPT',
    description: 'OpenAI\'s GPT models. Excellent reasoning and JSON output quality.',
    models: ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  },
  {
    value: 'ollama',
    label: 'Ollama (Local)',
    description: 'Run open-source models locally. 100% private, no API key needed.',
    models: ['deepseek-r1', 'llama3.2', 'mistral', 'phi4', 'qwen2.5'],
  },
];

export function AIConfig() {
  const queryClient = useQueryClient();
  const { data: config, isLoading } = useQuery<AIConfigType>({
    queryKey: ['ai-config'],
    queryFn: getAIConfig,
  });

  const [form, setForm] = useState({
    provider: 'gemini' as AIProvider,
    model_name: 'gemini-1.5-flash',
    api_key: '',
    ollama_base_url: 'http://localhost:11434',
    temperature: 0.1,
    max_tokens: 4096,
  });

  const [showKey, setShowKey] = useState(false);

  useEffect(() => {
    if (config) {
      setForm({
        provider: config.provider,
        model_name: config.model_name,
        api_key: '',
        ollama_base_url: config.ollama_base_url || 'http://localhost:11434',
        temperature: config.temperature,
        max_tokens: config.max_tokens,
      });
    }
  }, [config]);

  const updateMutation = useMutation({
    mutationFn: updateAIConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-config'] });
      toast.success('AI configuration updated!');
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to update config');
    },
  });

  const selectedProvider = PROVIDERS.find((p) => p.value === form.provider)!;

  const handleProviderChange = (provider: AIProvider) => {
    const p = PROVIDERS.find((x) => x.value === provider)!;
    setForm({ ...form, provider, model_name: p.models[0] });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: any = {
      provider: form.provider,
      model_name: form.model_name,
      ollama_base_url: form.ollama_base_url,
      temperature: form.temperature,
      max_tokens: form.max_tokens,
    };
    if (form.api_key.trim()) {
      payload.api_key = form.api_key.trim();
    }
    updateMutation.mutate(payload);
  };

  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center h-64 text-gray-400">
        Loading AI configuration...
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">AI Model Configuration</h1>
        <p className="text-sm text-gray-500 mt-1">Configure the AI provider used for CV parsing and formatting</p>
      </div>

      {/* Current Active Config Banner */}
      {config && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 mb-6 flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-indigo-500 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-indigo-900">
              Currently active: <span className="capitalize">{config.provider}</span> — {config.model_name}
            </p>
            <p className="text-xs text-indigo-600 mt-0.5">
              Temperature: {config.temperature} · Max tokens: {config.max_tokens}
            </p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Provider Selection */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
            <Bot className="w-4 h-4 text-indigo-500" />
            <h2 className="font-semibold text-gray-800 text-sm">AI Provider</h2>
          </div>
          <div className="p-5 grid grid-cols-1 sm:grid-cols-3 gap-3">
            {PROVIDERS.map((p) => (
              <button
                key={p.value}
                type="button"
                onClick={() => handleProviderChange(p.value)}
                className={`text-left p-4 rounded-xl border-2 transition ${
                  form.provider === p.value
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-200 hover:border-indigo-300 bg-gray-50'
                }`}
              >
                <p className={`font-semibold text-sm ${form.provider === p.value ? 'text-indigo-700' : 'text-gray-700'}`}>
                  {p.label}
                </p>
                <p className="text-xs text-gray-500 mt-1 leading-relaxed">{p.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Model Selection */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
            <ChevronDown className="w-4 h-4 text-indigo-500" />
            <h2 className="font-semibold text-gray-800 text-sm">Model</h2>
          </div>
          <div className="p-5">
            <label className="block text-sm text-gray-600 mb-2">Select model for {selectedProvider.label}</label>
            <select
              value={form.model_name}
              onChange={(e) => setForm({ ...form, model_name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {selectedProvider.models.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
            <p className="text-xs text-gray-400 mt-2">
              {form.provider === 'gemini' && 'Tip: gemini-1.5-flash is fast and has a generous free tier.'}
              {form.provider === 'openai' && 'Tip: gpt-4o-mini is the most cost-effective choice.'}
              {form.provider === 'ollama' && 'Tip: Run `ollama pull deepseek-r1` locally before using.'}
            </p>
          </div>
        </div>

        {/* Credentials */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
            <Key className="w-4 h-4 text-indigo-500" />
            <h2 className="font-semibold text-gray-800 text-sm">
              {form.provider === 'ollama' ? 'Ollama Server URL' : 'API Credentials'}
            </h2>
          </div>
          <div className="p-5">
            {form.provider === 'ollama' ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ollama Base URL</label>
                <div className="flex items-center gap-2">
                  <Server className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  <input
                    type="text"
                    value={form.ollama_base_url}
                    onChange={(e) => setForm({ ...form, ollama_base_url: e.target.value })}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="http://localhost:11434"
                  />
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  Default: http://localhost:11434. In Docker use http://host.docker.internal:11434
                </p>
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {form.provider === 'gemini' ? 'Gemini API Key' : 'OpenAI API Key'}
                </label>
                <div className="relative">
                  <input
                    type={showKey ? 'text' : 'password'}
                    value={form.api_key}
                    onChange={(e) => setForm({ ...form, api_key: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 pr-20"
                    placeholder="Leave blank to keep existing key"
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-indigo-600 hover:underline"
                  >
                    {showKey ? 'Hide' : 'Show'}
                  </button>
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  {form.provider === 'gemini'
                    ? 'Get your key from aistudio.google.com → API Keys'
                    : 'Get your key from platform.openai.com → API Keys'}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Fine-tuning */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-indigo-500" />
            <h2 className="font-semibold text-gray-800 text-sm">Fine-tuning</h2>
          </div>
          <div className="p-5 grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Temperature: <span className="text-indigo-600 font-bold">{form.temperature}</span>
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={form.temperature}
                onChange={(e) => setForm({ ...form, temperature: parseFloat(e.target.value) })}
                className="w-full accent-indigo-600"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>Precise (0)</span>
                <span>Creative (1)</span>
              </div>
              <p className="text-xs text-gray-400 mt-1">Recommended: 0.1 for accurate CV extraction</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Max Tokens</label>
              <input
                type="number"
                min="512"
                max="32768"
                step="512"
                value={form.max_tokens}
                onChange={(e) => setForm({ ...form, max_tokens: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <p className="text-xs text-gray-400 mt-1">Controls max output length. 4096 recommended.</p>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={updateMutation.isPending}
            className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg font-medium text-sm hover:bg-indigo-700 disabled:opacity-60 transition"
          >
            {updateMutation.isPending ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </form>
    </div>
  );
}
