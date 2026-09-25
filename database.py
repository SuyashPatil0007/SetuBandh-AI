import os
import urllib.parse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Check if Render (or cloud host) provided a DATABASE_URL environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # 2. Local fallback configuration
    DB_USER = "postgres"
    DB_PASSWORD = "suyash123"
    DB_HOST = "localhost"
    DB_PORT = "5432"
    DB_NAME = "setubandh_db"

    encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
    DATABASE_URL = (
        f"postgresql+psycopg2://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
else:
    # Render provides 'postgres://', which SQLAlchemy 1.4/2.0 requires as 'postgresql://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+psycopg2://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# Enable connection pre-ping to handle cloud timeouts gracefully
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# 3. Automatically enable PostGIS extension before tables are defined/created
try:
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()
    print("[+] Database: PostGIS extension verified/enabled successfully.")
except Exception as e:
    print(f"[-] Database Warning: PostGIS extension initialization bypassed or deferred: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()