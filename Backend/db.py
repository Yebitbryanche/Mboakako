from sqlmodel import create_engine, SQLModel


DB_NAME = "mboakako.db"
DB_URL = f"sqlite:///{DB_NAME}"

connect_args = {"check_same_thred":False}
engine = create_engine(DB_URL, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

