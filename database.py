import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Put the exact password you typed during the PostgreSQL installation:
DB_USER = "postgres"
DB_PASSWORD = "suyash123"  # <-- Replace with your real password
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "setubandh_db"

encoded_password = urllib.parse.quote_plus(DB_PASSWORD)

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()