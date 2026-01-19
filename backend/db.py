import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import SQLITE_DB_PATH

DB_URL = f"sqlite:///{SQLITE_DB_PATH}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class DebateLog(Base):
    __tablename__ = "debate_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    round_number = Column(Integer, nullable=False)
    agent_name = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    print(f"Initializing database at: {SQLITE_DB_PATH}")
    Base.metadata.create_all(bind=engine)
    print("Database initialization complete.")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def log_agent_message(session_id: str, round_number: int, agent_name: str, message: str):
    db = SessionLocal()
    try:
        log_entry = DebateLog(
            session_id=session_id,
            round_number=round_number,
            agent_name=agent_name,
            message=message
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
    except Exception as e:
        db.rollback()
        print(f"Error logging message for session {session_id}, round {round_number}, agent {agent_name}: {e}")
        raise e
    finally:
        db.close()

def get_session_history(session_id: str):
    db = SessionLocal()
    try:
        logs = (
            db.query(DebateLog)
            .filter(DebateLog.session_id == session_id)
            .order_by(DebateLog.id.asc())
            .all()
        )

        history = [
            {
                "round_number": log.round_number,
                "agent_name": log.agent_name,
                "message": log.message,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None # Format timestamp for JSON compatibility
            }
            for log in logs
        ]
        return history
    except Exception as e:
        print(f"Error retrieving history for session {session_id}: {e}")
        return []
    finally:
        db.close()

if __name__ == "__main__":
    print("Testing db.py...")
    try:
        init_db()
        print(f"Database file created/verified at: {SQLITE_DB_PATH}")

        dummy_session_id = "test_session_123"
        log_agent_message(
            session_id=dummy_session_id,
            round_number=1,
            agent_name="Test Agent",
            message="This is a test message."
        )
        print("Dummy message logged.")

        history = get_session_history(dummy_session_id)
        print(f"\nRetrieved history for {dummy_session_id}:")
        for entry in history:
            print(entry)

    except Exception as e:
        print(f"An error occurred during db.py test: {e}")