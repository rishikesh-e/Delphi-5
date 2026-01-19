import uuid
import os
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage
from fastapi.middleware.cors import CORSMiddleware

from backend.db import init_db
from backend.rag import add_file_to_knowledge_base, clear_knowledge_base
from backend.graph import app as graph_app, AgentState
from backend.config import Colors


app = FastAPI(
    title="AI Debate Orchestrator API",
    description="API for orchestrating AI agent debates with streaming responses.",
    version="1.0.0",
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_agent_color(name: str) -> str:
    if "Finance" in name:
        return Colors.FINANCE
    if "Risk" in name:
        return Colors.RISK
    if "Ethics" in name:
        return Colors.ETHICS
    if "Devil" in name:
        return Colors.DEVIL
    if "Tool" in name:
        return Colors.TOOL
    return Colors.MODERATOR

def print_separator(title: str = ""):
    print(f"\n{'=' * 20} {title} {'=' * 20}\n")

@app.on_event("startup")
async def startup_event():
    print("Initializing database...")
    init_db()
    print("Database initialized.")

@app.post("/ingest/clear")
async def clear_kb():
    clear_knowledge_base()
    return {"message": "Knowledge base cleared successfully."}

@app.post("/ingest/add")
async def add_kb_file(file_path: str):
    file_path = file_path.strip('"').strip("'")
    if os.path.exists(file_path):
        result = add_file_to_knowledge_base(file_path)
        return {"message": f"File '{file_path}' processed.", "details": result}
    else:
        return {"error": f"File not found at path: {file_path}"}, 404


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print(f"WebSocket connection accepted from {websocket.client.host}:{websocket.client.port}")
    try:
        while True:
            data = await websocket.receive_json()
            user_query = data.get("user_query")

            if not user_query:
                await websocket.send_json({"type": "error", "message": "No user_query provided"})
                continue

            session_id = str(uuid.uuid4())
            print(f"Starting debate session ID: {session_id} for query: '{user_query}'")

            initial_state: AgentState = {
                "session_id": session_id,
                "user_query": user_query,
                "rag_context": "",
                "round_number": 1,
                "messages": [],
                "tool_output": {},
                "tool_calls_to_execute": []
            }

            # Stream LangChain graph output over WebSocket
            async for event in graph_app.astream(initial_state, stream_mode="updates"):
                for _, update in event.items():
                    messages = update.get("messages", [])
                    tool_outputs = update.get("tool_output", {})

                    # Send tool results if any
                    if tool_outputs:
                        await websocket.send_json({"type": "tool_output", "data": tool_outputs})

                    # Send AIMessage content
                    for msg in messages:
                        if isinstance(msg, AIMessage) and msg.content.strip():
                            await websocket.send_json({
                                "type": "ai_message",
                                "name": msg.name,
                                "content": msg.content
                            })
                    for msg in messages:
                        print("MSG:", msg, "NAME:", msg.name)
            await websocket.send_json({"type": "debate_finished", "session_id": session_id})
            print(f"Debate finished for session ID: {session_id}")

    except WebSocketDisconnect:
        print(f"WebSocket connection closed for {websocket.client.host}:{websocket.client.port}")
    except Exception as e:
        print(f"An error occurred in WebSocket: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})

@app.post("/stream")
async def stream_debate_sse(request: Request):
    try:
        data = await request.json()
        user_query = data.get("user_query")

        if not user_query:
            return StreamingResponse(
                iter(["data: {\"type\": \"error\", \"message\": \"No user_query provided\"}\n\n"]),
                media_type="text/event-stream"
            )

        session_id = str(uuid.uuid4())
        print(f"Starting SSE debate session ID: {session_id} for query: '{user_query}'")

        initial_state: AgentState = {
            "session_id": session_id,
            "user_query": user_query,
            "rag_context": "",
            "round_number": 1,
            "messages": [],
            "tool_output": {},
            "tool_calls_to_execute": []
        }

        async def generate_stream():
            try:
                async for event in graph_app.astream(
                        initial_state,
                        stream_mode="updates"
                ):
                    for _, update in event.items():
                        messages = update.get("messages", [])
                        tool_outputs = update.get("tool_output", {})

                        if tool_outputs:
                            yield f"event: tool_output\ndata: {json.dumps(tool_outputs)}\n\n"

                        for msg in messages:
                            if isinstance(msg, AIMessage) and msg.content.strip():
                                yield (
                                    "event: ai_message\n"
                                    f"data: {json.dumps({'name': msg.name, 'content': msg.content})}\n\n"
                                )

                yield f"event: debate_finished\ndata: {json.dumps({'session_id': session_id})}\n\n"


            except Exception as e:
                print(f"An error occurred during SSE streaming: {e}")
                yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

    except Exception as e:
        print(f"An error occurred in SSE endpoint: {e}")
        return StreamingResponse(
            iter([f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"]),
            media_type="text/event-stream"
        )


if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI server with uvicorn...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)