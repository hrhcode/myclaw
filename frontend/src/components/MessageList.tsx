import ReactMarkdown from 'react-markdown';
import { Message } from '../types';

interface MessageListProps {
  messages: Message[];
}

/**
 * 消息列表组件 - 显示对话中的所有消息
 */
const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 ? (
        <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400">
          <div className="text-center">
            <svg className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p className="text-lg">开始新的对话</p>
            <p className="text-sm mt-2">输入消息开始与AI对话</p>
          </div>
        </div>
      ) : (
        messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white'
              }`}
            >
              <div className="text-sm font-medium mb-1 opacity-75">
                {message.role === 'user' ? '你' : 'AI助手'}
              </div>
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
};

export default MessageList;
