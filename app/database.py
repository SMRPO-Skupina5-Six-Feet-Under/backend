import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import psycopg2


hostname = os.getenv("POSTGRES_HOST", "localhost")
username = os.getenv("POSTGRES_USER", "dbuser")
password = os.getenv("POSTGRES_PASSWORD", "postgres")
database = os.getenv("POSTGRES_DB", "smrpo-db")
SQLALCHEMY_DATABASE_URL = f"postgresql://{username}:{password}@{hostname}:5432" \
                          f"/{database}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()