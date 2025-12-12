import uuid
import os
import sys
from backend.db import init_db
from backend.rag import add_file_to_knowledge_base, clear_knowledge_base
from backend.graph import app as graph_app

class Colors:
    FINANCE = '\033[94m'
    RISK = '\033[91m'
    ETHICS = '\033[92m'
    DEVIL = '\033[93m'
    MODERATOR = '\033[95m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def get_agent_color(name):
    if "Finance" in name: return Colors.FINANCE
    if "Risk" in name: return Colors.RISK
    if "Ethics" in name: return Colors.ETHICS
    if "Devil" in name: return Colors.DEVIL
    return Colors.MODERATOR


def print_separator(title=""):
    print(f"\n{Colors.BOLD}{'=' * 20} {title} {'=' * 20}{Colors.RESET}\n")


def ingest_documents():
    print_separator("KNOWLEDGE BASE SETUP")

    choice = input("Do you want to ingest documents before the debate? (y/n): ").lower()
    if choice != 'y':
        return

    if input("Clear existing knowledge base? (y/n): ").lower() == 'y':
        clear_knowledge_base()
        print("Knowledge base cleared.")

    while True:
        file_path = input("\nEnter full file path (PDF/TXT) or 'done' to finish: ").strip()

        if file_path.lower() == 'done':
            break

        file_path = file_path.strip('"').strip("'")

        if os.path.exists(file_path):
            try:
                print(f"Processing {file_path}...")
                msg = add_file_to_knowledge_base(file_path)
                print(f"{Colors.ETHICS}✔ {msg}{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RISK}✘ Error processing file: {e}{Colors.RESET}")
        else:
            print(f"{Colors.RISK}✘ File not found.{Colors.RESET}")


def run_debate():
    print_separator("AI FINANCE BOARDROOM")

    user_query = input(f"{Colors.BOLD}Enter the financial problem/query:\n> {Colors.RESET}")
    if not user_query.strip():
        print("Query cannot be empty.")
        return

    session_id = str(uuid.uuid4())
    print(f"\nSession ID: {session_id}")
    print("The Board is deliberating... (This may take a minute)\n")

    initial_state = {
        "session_id": session_id,
        "user_query": user_query,
        "rag_context": "",
        "round_number": 1,
        "messages": []
    }

    current_round = 1

    for event in graph_app.stream(initial_state):

        messages_to_print = []

        if "analysts" in event:
            messages_to_print = event["analysts"]["messages"]
            print_separator(f"ROUND {current_round} - ANALYSTS SPEAK")

        elif "moderator" in event:
            messages_to_print = event["moderator"]["messages"]
            print_separator(f"ROUND {current_round} - MODERATOR SUMMARY")
            current_round += 1

        for msg in messages_to_print:
            name = msg.name
            content = msg.content
            clean_content = content.replace(f"[{name}]: ", "")
            color = get_agent_color(name)

            print(f"{color}{Colors.BOLD}[{name}]{Colors.RESET}")
            print(f"{clean_content}")
            print("-" * 50)

    print_separator("DEBATE FINISHED")
    print(f"Session Log saved to database with ID: {session_id}")

if __name__ == "__main__":
    print("")
    try:
        init_db()
        print("Database initialized.")

        ingest_documents()
        run_debate()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RISK}An error occurred: {e}{Colors.RESET}")