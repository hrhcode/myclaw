import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getProviders, getProviderModels, getConfig, setConfig } from '../services/api';
import type { Provider, Model } from '../types';

const Settings: React.FC = () => {
  const navigate = useNavigate();
  const [providers, setProviders] = useState<Provider[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [apiKey, setApiKey] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  useEffect(() => {
    if (selectedProvider) {
      loadModels(selectedProvider);
    }
  }, [selectedProvider]);

  const loadSettings = async () => {
    try {
      setIsLoading(true);

      const providerList = await getProviders();
      setProviders(providerList);

      const savedProvider = await getConfig('llm_provider').catch(() => '');
      const savedModel = await getConfig('llm_model').catch(() => '');
      const savedApiKey = await getConfig('zhipu_api_key').catch(() => '');

      if (savedProvider) {
        setSelectedProvider(savedProvider);
      } else if (providerList.length > 0) {
        setSelectedProvider(providerList[0].id);
      }

      if (savedApiKey) {
        setApiKey(savedApiKey);
      }

      if (savedModel) {
        setSelectedModel(savedModel);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
      setMessage({ type: 'error', text: '加载设置失败' });
    } finally {
      setIsLoading(false);
    }
  };

  const loadModels = async (provider: string) => {
    try {
      const modelList = await getProviderModels(provider);
      setModels(modelList);

      if (selectedModel && !modelList.find(m => m.id === selectedModel)) {
        setSelectedModel(modelList.length > 0 ? modelList[0].id : '');
      } else if (modelList.length > 0 && !selectedModel) {
        setSelectedModel(modelList[0].id);
      }
    } catch (error) {
      console.error('Failed to load models:', error);
    }
  };

  const handleSave = async () => {
    if (!apiKey.trim()) {
      setMessage({ type: 'error', text: '请输入API Key' });
      return;
    }

    if (!selectedProvider) {
      setMessage({ type: 'error', text: '请选择LLM提供商' });
      return;
    }

    if (!selectedModel) {
      setMessage({ type: 'error', text: '请选择模型' });
      return;
    }

    try {
      setIsSaving(true);
      setMessage(null);

      await setConfig('zhipu_api_key', apiKey);
      await setConfig('llm_provider', selectedProvider);
      await setConfig('llm_model', selectedModel);

      setMessage({ type: 'success', text: '设置保存成功！' });
    } catch (error) {
      console.error('Failed to save settings:', error);
      setMessage({ type: 'error', text: '保存设置失败' });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-gray-600 dark:text-gray-300">加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <div className="max-w-2xl mx-auto py-8 px-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">设置</h1>
            <Link
              to="/"
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              返回对话
            </Link>
          </div>

          {message && (
            <div
              className={`mb-4 p-4 rounded-lg ${
                message.type === 'success'
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
              }`}
            >
              {message.text}
            </div>
          )}

          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">LLM配置</h2>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  模型厂商
                </label>
                <select
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="">请选择厂商</option>
                  {providers.map((provider) => (
                    <option key={provider.id} value={provider.id}>
                      {provider.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  模型
                </label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  disabled={!selectedProvider}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white disabled:opacity-50"
                >
                  <option value="">请先选择厂商</option>
                  {models.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">API配置</h2>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  智谱AI API Key
                </label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="请输入您的API Key"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                />
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  API Key将安全存储在数据库中
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={() => navigate('/')}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
              >
                {isSaving ? '保存中...' : '保存设置'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;