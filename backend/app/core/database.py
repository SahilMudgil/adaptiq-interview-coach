import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

logger = logging.getLogger("uvicorn.error")

engine = None
is_postgres = False
has_pgvector = False

# Try PostgreSQL first
try:
    test_engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3}
    )
    with test_engine.connect() as conn:
        conn.execute(text("SELECT 1;"))
        # Check pgvector
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            has_pgvector = True
            logger.info("Connected to PostgreSQL with pgvector extension enabled.")
        except Exception:
            logger.warning("Connected to PostgreSQL, but pgvector extension is not installed. Using array/json fallback.")
    engine = test_engine
    is_postgres = True
except Exception as e:
    logger.warning(
        f"Could not connect to PostgreSQL ({e}). "
        f"Falling back to SQLite database ({settings.FALLBACK_SQLITE_URL}) for seamless local development."
    )
    engine = create_engine(
        settings.FALLBACK_SQLITE_URL,
        connect_args={"check_same_thread": False}
    )
    is_postgres = False
    has_pgvector = False

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
