import { useState, useEffect } from 'react';

interface SettingsProps {
  apiKey: string;
  onApiKeyChange: (apiKey: string) => void;
}

/**
 * 设置组件 - 用于配置API Key
 */
const Settings: React.FC<SettingsProps> = ({ apiKey, onApiKeyChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [tempApiKey, setTempApiKey] = useState(apiKey);

  useEffect(() => {
    setTempApiKey(apiKey);
  }, [apiKey]);

  const handleSave = () => {
    onApiKeyChange(tempApiKey);
    setIsOpen(false);
  };

  const handleCancel = () => {
    setTempApiKey(apiKey);
    setIsOpen(false);
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
      >
        设置
      </button>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">设置</h2>
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
            智谱AI API Key
          </label>
          <input
            type="password"
            value={tempApiKey}
            onChange={(e) => setTempApiKey(e.target.value)}
            placeholder="请输入您的API Key"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
          />
        </div>
        <div className="flex justify-end gap-2">
          <button
            onClick={handleCancel}
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            保存
          </button>
        </div>
      </div>
    </div>
  );
};

export default Settings;
