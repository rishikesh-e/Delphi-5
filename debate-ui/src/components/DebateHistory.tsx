import React from "react";
import { DebateSession } from "../types";
import "../styles.css";

interface Props {
  sessions: DebateSession[];
  activeSessionId: string | null;
  onSelect: (id: string) => void;
}

const DebateHistory: React.FC<Props> = ({
  sessions,
  activeSessionId,
  onSelect,
}) => {
  return (
    <div className="sidebar">
      <h3>Debate History</h3>

      {sessions.map((session) => (
        <div
          key={session.sessionId}
          className={`history-item ${
            session.sessionId === activeSessionId ? "active" : ""
          }`}
          onClick={() => onSelect(session.sessionId)}
        >
          {session.title}
        </div>
      ))}
    </div>
  );
};

export default DebateHistory;
