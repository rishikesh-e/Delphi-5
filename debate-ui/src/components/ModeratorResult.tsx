import React from "react";

interface Props {
  messages: string[];
}

const ModeratorResult: React.FC<Props> = ({ messages }) => {
  if (messages.length === 0) return null;

  return (
    <div className="moderator">
      <h2>Moderator Final Decision</h2>
      {messages.map((msg, i) => (
        <p key={i}>{msg}</p>
      ))}
    </div>
  );
};

export default ModeratorResult;
