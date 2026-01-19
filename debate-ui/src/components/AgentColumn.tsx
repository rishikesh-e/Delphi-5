import React from "react";
import "../styles.css";

interface Props {
  name: string;
  messages: string[];
}

const AgentColumn: React.FC<Props> = ({ name, messages }) => {
  return (
    <div className="agent-column">
      <h3>{name}</h3>
      <div className="agent-messages">
        {messages.map((msg, i) => (
          <div key={i} className="message">
            {msg}
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentColumn;
