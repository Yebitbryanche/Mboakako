from datetime import timedelta
from fastapi import FastAPI,Depends, HTTPException
from fastapi.security import  OAuth2PasswordRequestForm
from typing import Annotated
from sqlmodel import Session, select
from models import Token, User, UserRead
from pydantic import EmailStr
from auth import authenticate_user, create_access_token, get_current_user
from db import engine, create_db_and_tables

ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]


app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


### Register new user into the system
@app.post("/signup", response_model=UserRead)
def signup(user_name:str, email:EmailStr, password:str, session:SessionDep):
    existing_user = session.exec(select(User).where(User.user_name == user_name)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Usename already registered")
    user = User(user_name=user_name, email=email)
    user.set_password(password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.post("/login", response_model=Token)
def login(session:SessionDep, form_data:  OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub":user.user_name},
                                       expires_delta=timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
                                       )
    return {"access_token":access_token, "token_type":"bearer"}


@app.get("/users/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

