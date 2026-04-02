import { useNavigate } from 'react-router-dom';

import { useApp } from '../../contexts/AppContext';

const SessionSelect: React.FC = () => {
  const navigate = useNavigate();
  const { sessions, currentSessionId, selectSession } = useApp();

  return (
    <select
      className="admin-select px-3 py-2.5 min-w-[180px]"
      value={currentSessionId ?? ''}
      aria-label="选择工作会话"
      title="选择工作会话"
      onChange={(event) => {
        const nextId = Number(event.target.value);
        selectSession(Number.isNaN(nextId) ? null : nextId);
        navigate('/chat');
      }}
    >
      {sessions.map((session) => (
        <option key={session.id} value={session.id}>
          {`工作会话：${session.name}`}
        </option>
      ))}
    </select>
  );
};

export default SessionSelect;
