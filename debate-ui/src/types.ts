export type AgentName =
  | "Finance Analyst"
  | "Risk Analyst"
  | "Ethics Analyst"
  | "Devil's Advocate"
  | "Moderator";


export interface AIMessage {
  type: "ai_message";
  name: AgentName;
  content: string;
}

export interface DebateRound {
  roundNumber: number;
  messages: Record<AgentName, string[]>;
}

export interface ToolOutput {
  type: "tool_output";
  data: Record<string, any>;
}

export interface DebateSession {
  sessionId: string;
  title: string;
  rounds: DebateRound[];
  moderatorMessages: string[];
}

