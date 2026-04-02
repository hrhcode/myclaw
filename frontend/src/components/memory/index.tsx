import { useState } from 'react';

import MainLayout from '../layout/MainLayout';
import ConfigTab from './ConfigTab';
import LongTermMemoryTab from './LongTermMemoryTab';
import { SegmentedTabs } from '../admin';

const MemoryPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'config' | 'memory'>('config');

  return (
    <MainLayout headerTitle="记忆">
      <div className="admin-page">
        <div className="memory-page-shell h-full">
          <SegmentedTabs
            tabs={[
              { key: 'config', label: '记忆设置' },
              { key: 'memory', label: '长期记忆' },
            ]}
            activeKey={activeTab}
            onChange={(key) => setActiveTab(key as 'config' | 'memory')}
          />

          <div className="memory-page-content flex-1 min-h-0 overflow-y-auto">
            {activeTab === 'config' ? <ConfigTab /> : <LongTermMemoryTab />}
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default MemoryPage;
