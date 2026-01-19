import React from "react";
import AgentColumn from "./AgentColumn";
import { AgentName } from "../types";

interface Props {
  roundNumber: number;
  messages: Record<AgentName, string[]>;
}

const agents: AgentName[] = [
  "Finance Analyst",
  "Risk Analyst",
  "Ethics Analyst",
  "Devil's Advocate",
];

const DebateRound: React.FC<Props> = ({ roundNumber, messages }) => {
  return (
    <div className="round">
      <h2>Round {roundNumber}</h2>
      <div className="round-grid">
        {agents.map((agent) => (
          <AgentColumn
            key={agent}
            name={agent}
            messages={messages[agent] || []}
          />
        ))}
      </div>
    </div>
  );
};

export default DebateRound;
