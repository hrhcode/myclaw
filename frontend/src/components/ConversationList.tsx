import { Conversation } from '../types';

interface ConversationListProps {
  conversations: Conversation[];
  currentConversationId: number | null;
  onSelectConversation: (id: number) => void;
  onCreateConversation: () => void;
  onDeleteConversation: (id: number) => void;
}

/**
 * 会话列表组件 - 显示和管理所有对话会话
 */
const ConversationList: React.FC<ConversationListProps> = ({
  conversations,
  currentConversationId,
  onSelectConversation,
  onCreateConversation,
  onDeleteConversation,
}) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  return (
    <div className="w-64 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={onCreateConversation}
          className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center justify-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          新建对话
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-4 text-center text-gray-500 dark:text-gray-400">
            暂无对话
          </div>
        ) : (
          conversations.map((conversation) => (
            <div
              key={conversation.id}
              className={`p-4 border-b border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors group ${
                currentConversationId === conversation.id
                  ? 'bg-purple-50 dark:bg-purple-900/20 border-l-4 border-l-purple-600'
                  : ''
              }`}
            >
              <div
                className="flex items-center justify-between"
                onClick={() => onSelectConversation(conversation.id)}
              >
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {conversation.title}
                  </h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {formatDate(conversation.updated_at)}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm('确定要删除这个对话吗？')) {
                      onDeleteConversation(conversation.id);
                    }
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ConversationList;
