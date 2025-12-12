import operator
from typing import Annotated, List, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END

from backend.llm import get_llm
from backend.prompts import get_system_prompt
from backend.db import log_agent_message
from backend.rag import query_knowledge_base


class AgentState(TypedDict):
    session_id: str
    user_query: str
    rag_context: str
    round_number: int
    messages: Annotated[List[BaseMessage], operator.add]


def retrieve_context_node(state: AgentState):
    query = state["user_query"]
    context = query_knowledge_base(query, k=3)
    return {"rag_context": context}


def run_analyst(agent_name: str, state: AgentState):
    round_num = state["round_number"]
    query = state["user_query"]
    context = state["rag_context"]
    history = state["messages"]

    sys_prompt = get_system_prompt(agent_name, round_num)

    messages = [
        SystemMessage(content=sys_prompt),
        HumanMessage(content=f"User Query: {query}\n\nContext from Documents:\n{context}")
    ]

    messages.extend(history)

    messages.append(
        HumanMessage(
            content=f"You are the {agent_name}. Based on the conversation above, please provide your response now.")
    )

    llm = get_llm()
    response = llm.invoke(messages)
    content = response.content

    log_agent_message(
        session_id=state["session_id"],
        round_number=round_num,
        agent_name=agent_name,
        message=content
    )

    return AIMessage(content=f"[{agent_name}]: {content}", name=agent_name)


def analysts_node(state: AgentState):
    finance_msg = run_analyst("Finance Analyst", state)
    risk_msg = run_analyst("Risk Analyst", state)
    ethics_msg = run_analyst("Ethics Analyst", state)
    devil_msg = run_analyst("Devil's Advocate", state)

    return {
        "messages": [finance_msg, risk_msg, ethics_msg, devil_msg]
    }


def moderator_node(state: AgentState):
    round_num = state["round_number"]

    mod_msg = run_analyst("Moderator", state)

    return {
        "messages": [mod_msg],
        "round_number": round_num + 1
    }


def should_continue(state: AgentState):
    if state["round_number"] <= 2:
        return "continue"
    else:
        return "end"


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("analysts", analysts_node)
    workflow.add_node("moderator", moderator_node)

    workflow.set_entry_point("retrieve_context")
    workflow.add_edge("retrieve_context", "analysts")
    workflow.add_edge("analysts", "moderator")


    workflow.add_conditional_edges(
        "moderator",
        should_continue,
        {
            "continue": "analysts",
            "end": END
        }
    )

    return workflow.compile()


app = build_graph()