import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Save, Key, Cpu, CheckCircle, AlertCircle, Loader2, Eye, EyeOff } from 'lucide-react';
import { getProviders, getProviderModels, getConfig, setConfig } from '../services/api';
import type { Provider, Model } from '../types';

/**
 * 设置页面组件 - 配置API和模型参数
 * 采用玻璃拟态设计，支持动画效果和主题切换
 */
const Settings: React.FC = () => {
  const navigate = useNavigate();
  const [providers, setProviders] = useState<Provider[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [apiKey, setApiKey] = useState<string>('');
  const [showApiKey, setShowApiKey] = useState(false);
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

  /**
   * 加载设置数据
   */
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

  /**
   * 加载模型列表
   */
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

  /**
   * 保存设置
   */
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
      
      setTimeout(() => {
        navigate('/');
      }, 1500);
    } catch (error) {
      console.error('Failed to save settings:', error);
      setMessage({ type: 'error', text: '保存设置失败' });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        >
          <Loader2 size={40} className="text-primary" />
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-8" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="max-w-2xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="glass-card rounded-2xl p-6 md:p-8"
        >
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>设置</h1>
              <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>配置您的AI助手参数</p>
            </div>
            <Link
              to="/"
              className="btn-secondary flex items-center gap-2"
            >
              <ArrowLeft size={18} />
              <span>返回</span>
            </Link>
          </div>

          <AnimatePresence mode="wait">
            {message && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className={`mb-6 p-4 rounded-xl flex items-center gap-3 ${
                  message.type === 'success'
                    ? 'bg-green-500/10 border border-green-500/20 text-green-400'
                    : 'bg-red-500/10 border border-red-500/20 text-red-400'
                }`}
              >
                {message.type === 'success' ? (
                  <CheckCircle size={20} />
                ) : (
                  <AlertCircle size={20} />
                )}
                <span>{message.text}</span>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="space-y-8">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/20 to-primary-dark/20 flex items-center justify-center">
                  <Cpu size={20} className="text-primary" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>LLM配置</h2>
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>选择AI模型提供商和模型</p>
                </div>
              </div>

              <div className="space-y-4 pl-13">
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>
                    模型厂商
                  </label>
                  <select
                    value={selectedProvider}
                    onChange={(e) => setSelectedProvider(e.target.value)}
                    className="w-full px-4 py-3 glass-input rounded-xl appearance-none cursor-pointer"
                    style={{ 
                      color: 'var(--text-primary)',
                      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='${encodeURIComponent('var(--text-muted)')}'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
                      backgroundRepeat: 'no-repeat',
                      backgroundPosition: 'right 1rem center',
                      backgroundSize: '1.5rem'
                    }}
                  >
                    <option value="">请选择厂商</option>
                    {providers.map((provider) => (
                      <option key={provider.id} value={provider.id}>
                        {provider.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>
                    模型
                  </label>
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    disabled={!selectedProvider}
                    className="w-full px-4 py-3 glass-input rounded-xl appearance-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{ 
                      color: 'var(--text-primary)',
                      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='${encodeURIComponent('var(--text-muted)')}'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
                      backgroundRepeat: 'no-repeat',
                      backgroundPosition: 'right 1rem center',
                      backgroundSize: '1.5rem'
                    }}
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
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/20 to-primary-dark/20 flex items-center justify-center">
                  <Key size={20} className="text-primary" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>API配置</h2>
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>配置您的API密钥</p>
                </div>
              </div>

              <div className="space-y-4 pl-13">
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>
                    API Key
                  </label>
                  <div className="relative">
                    <input
                      type={showApiKey ? 'text' : 'password'}
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="请输入您的API Key"
                      className="w-full px-4 py-3 pr-12 glass-input rounded-xl"
                      style={{ color: 'var(--text-primary)' }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 transition-colors"
                      style={{ color: 'var(--text-muted)' }}
                      onMouseEnter={(e) => e.currentTarget.style.color = 'var(--text-primary)'}
                      onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
                    >
                      {showApiKey ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                  <p className="mt-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                    API Key将安全存储在数据库中，不会泄露给第三方
                  </p>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="flex justify-end gap-3 pt-6"
              style={{ borderTop: '1px solid var(--glass-border)' }}
            >
              <button
                onClick={() => navigate('/')}
                className="btn-secondary"
              >
                取消
              </button>
              <motion.button
                onClick={handleSave}
                disabled={isSaving}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="btn-primary flex items-center gap-2"
              >
                {isSaving ? (
                  <>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    >
                      <Loader2 size={18} />
                    </motion.div>
                    <span>保存中...</span>
                  </>
                ) : (
                  <>
                    <Save size={18} />
                    <span>保存设置</span>
                  </>
                )}
              </motion.button>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Settings;
