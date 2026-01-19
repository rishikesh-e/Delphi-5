import React, { useRef, useState } from "react";
import DebateRound from "./components/DebateRound";
import ModeratorResult from "./components/ModeratorResult";
import ChatInput from "./components/ChatInput";
import DebateHistory from "./components/DebateHistory";
import { DebateSession, AgentName } from "./types";

const isAgentName = (name: string): name is AgentName => {
  return (
    name === "Finance Analyst" ||
    name === "Risk Analyst" ||
    name === "Ethics Analyst" ||
    name === "Devil's Advocate" ||
    name === "Moderator"
  );
};

/* ---------- HELPERS ---------- */
const createEmptyMessages = () => ({
  "Finance Analyst": [],
  "Risk Analyst": [],
  "Ethics Analyst": [],
  "Devil's Advocate": [],
  "Moderator": [],
});

const App: React.FC = () => {
  const wsRef = useRef<WebSocket | null>(null);

  const [sessions, setSessions] = useState<DebateSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [currentRound, setCurrentRound] = useState(1);

  const activeSession = sessions.find(
    (s) => s.sessionId === activeSessionId
  );

  const initWebSocket = () => {
    wsRef.current = new WebSocket("ws://127.0.0.1:8000/ws");


    wsRef.current.onmessage = (event) => {
      console.log("RAW WS MESSAGE:", event.data);
      const data = JSON.parse(event.data);

      if (!activeSessionId) return;

      if (data.type === "ai_message") {
        const { name, content } = data;

        if (!isAgentName(name)) return;

        setSessions((prev) =>
          prev.map((s) => {
            if (s.sessionId !== activeSessionId) return s;

            // Moderator messages
            if (name === "Moderator") {
              return {
                ...s,
                moderatorMessages: [...s.moderatorMessages, content],
              };
            }

            let round = s.rounds.find(
              (r) => r.roundNumber === currentRound
            );

            if (!round) {
              round = {
                roundNumber: currentRound,
                messages: createEmptyMessages(),
              };
              s.rounds.push(round);
            }

            round.messages[name].push(content);

            return { ...s };
          })
        );
      }

      if (data.type === "debate_finished") {
        setCurrentRound((r) => r + 1);
      }
    };
  };

  /* ---------- SEND QUERY ---------- */
  const sendQuery = (query: string) => {
    const sessionId = crypto.randomUUID();

    const newSession: DebateSession = {
      sessionId,
      title: query.slice(0, 40),
      rounds: [],
      moderatorMessages: [],
    };

    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(sessionId);
    setCurrentRound(1);

    initWebSocket();

    setTimeout(() => {
      wsRef.current?.send(JSON.stringify({ user_query: query }));
    }, 300);
  };

  /* ---------- UI ---------- */
  return (
    <div className="layout">
      <DebateHistory
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelect={setActiveSessionId}
      />

      <div className="main">
        {activeSession?.rounds.map((round) => (
          <DebateRound
            key={round.roundNumber}
            roundNumber={round.roundNumber}
            messages={round.messages}
          />
        ))}

        <ModeratorResult
          messages={activeSession?.moderatorMessages || []}
        />

        <ChatInput onSend={sendQuery} />
      </div>
    </div>
  );
};

export default App;
