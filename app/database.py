from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql+psycopg2://postgres:mysecretpassword@postgres_db_container/database')

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
