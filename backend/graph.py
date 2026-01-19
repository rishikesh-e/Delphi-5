import operator
import json
from typing import Annotated, List, TypedDict, Dict, Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END

from backend.llm import get_llm
from backend.prompts import get_system_prompt
from backend.db import log_agent_message
from backend.rag import query_knowledge_base

import numpy_financial as npf


def calculate_npv(initial_investment: float, cash_flows: List[float], discount_rate: float) -> float:
    return -initial_investment + sum(
        cf / ((1 + discount_rate) ** (i + 1))
        for i, cf in enumerate(cash_flows)
    )


def calculate_irr(initial_investment: float, cash_flows: List[float]) -> float:
    return npf.irr([-initial_investment] + cash_flows)


def calculate_roi(investment: float, profit: float) -> float:
    return (profit / investment) * 100 if investment else 0.0


TOOL_MAP = {
    "calculate_npv": calculate_npv,
    "calculate_irr": calculate_irr,
    "calculate_roi": calculate_roi,
}


class AgentState(TypedDict):
    session_id: str
    user_query: str
    rag_context: str
    round_number: int
    messages: Annotated[List[BaseMessage], operator.add]
    tool_calls_to_execute: List[Dict[str, Any]]
    tool_output: Dict[str, Any]


def retrieve_context_node(state: AgentState):
    context = query_knowledge_base(state["user_query"], k=3)
    return {"rag_context": context or ""}


def run_agent(agent_name: str, state: AgentState) -> Dict[str, Any]:
    llm = get_llm()
    sys_prompt = get_system_prompt(agent_name, state["round_number"])

    messages = [
        SystemMessage(content=sys_prompt),
        HumanMessage(content=state["user_query"]),
    ]

    messages.extend(state["messages"])

    if state["tool_output"]:
        messages.append(
            HumanMessage(
                content=f"Previous tool results:\n{json.dumps(state['tool_output'], indent=2)}"
            )
        )

    response = llm.invoke(messages)
    content = response.content.strip()

    log_agent_message(
        session_id=state["session_id"],
        round_number=state["round_number"],
        agent_name=agent_name,
        message=content
    )

    try:
        tool_json = json.loads(content)
        if "tool" in tool_json and "parameters" in tool_json:
            return {
                "messages": [
                    AIMessage(
                        content=f"{agent_name} requested tool `{tool_json['tool']}`",
                        name=agent_name
                    )
                ],
                "tool_calls_to_execute": [{
                    "agent_name": agent_name,
                    "tool_name": tool_json["tool"],
                    "parameters": tool_json["parameters"]
                }]
            }
    except Exception:
        pass

    return {
        "messages": [
            AIMessage(content=content, name=agent_name)
        ]
    }


def analysts_node(state: AgentState):
    messages = []
    tool_calls = []

    for agent in [
        "Finance Analyst",
        "Risk Analyst",
        "Ethics Analyst",
        "Devil's Advocate"
    ]:
        delta = run_agent(agent, state)
        messages.extend(delta.get("messages", []))
        tool_calls.extend(delta.get("tool_calls_to_execute", []))

    return {
        "messages": messages,
        "tool_calls_to_execute": tool_calls
    }


def execute_tools_node(state: AgentState):
    outputs = {}

    for call in state["tool_calls_to_execute"]:
        fn = TOOL_MAP[call["tool_name"]]
        outputs[call["tool_name"]] = fn(**call["parameters"])

    return {
        "tool_output": outputs,
        "tool_calls_to_execute": []
    }


def moderator_node(state: AgentState):
    delta = run_agent("Moderator", state)
    return {
        "messages": delta["messages"],
        "round_number": state["round_number"] + 1,
        "tool_output": {}
    }


def verdict_node(state: AgentState):
    llm = get_llm()

    instruction = (
        "The debate rounds are finished. You are the Moderator. "
        "Review the entire discussion above. "
        "Provide a final, comprehensive verdict, summarizing the key points from "
        "Finance, Risk, Ethics, and the Devil's Advocate. "
        "Conclude with a clear recommendation for the user."
    )

    messages = state["messages"] + [HumanMessage(content=instruction)]

    response = llm.invoke(messages)
    content = response.content.strip()

    log_agent_message(
        session_id=state["session_id"],
        round_number=state["round_number"],
        agent_name="Moderator",
        message=content
    )

    return {
        "messages": [AIMessage(content=content, name="Moderator")]
    }


def should_continue(state: AgentState):
    return "continue" if state["round_number"] <= 2 else "end"


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("retrieve_context", retrieve_context_node)
    g.add_node("analysts", analysts_node)
    g.add_node("execute_tools", execute_tools_node)
    g.add_node("moderator", moderator_node)

    g.add_node("verdict", verdict_node)

    g.set_entry_point("retrieve_context")
    g.add_edge("retrieve_context", "analysts")

    g.add_conditional_edges(
        "analysts",
        lambda s: "execute_tools" if s["tool_calls_to_execute"] else "moderator",
        {
            "execute_tools": "execute_tools",
            "moderator": "moderator"
        }
    )

    g.add_edge("execute_tools", "moderator")

    g.add_conditional_edges(
        "moderator",
        should_continue,
        {
            "continue": "analysts",
            "end": "verdict"
        }
    )

    g.add_edge("verdict", END)

    return g.compile()


app = build_graph()