import React, { useState } from "react";
import "../styles.css";

interface Props {
  onSend: (query: string) => void;
}

const ChatInput: React.FC<Props> = ({ onSend }) => {
  const [value, setValue] = useState("");

  return (
    <div className="chat-input">
      <input
        placeholder="Ask something..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && onSend(value)}
      />
      <button onClick={() => onSend(value)}>Send</button>
    </div>
  );
};

export default ChatInput;
