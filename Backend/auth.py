from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, Annotated
from jose import jwt, JWTError
from models import User
from db import engine
from sqlmodel import select, Session


def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]


SECRET_KEY = "741sdf852re3sdf0sdr7rtjb455s741fgas411f7896214852815rf517416"
ALGORITHM = "HS256"


oauth2_bearer = OAuth2PasswordBearer(tokenUrl='login')


## function to create JWT access token
def create_access_token(data:dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_user(session:SessionDep, username:str) -> Optional[User]:
    return session.exec(select(User).where(User.user_name == username)).first()

def authenticate_user(session:SessionDep, username:str, password:str):
    user = get_user(session,username)
    if not user or not user.check_password(password):
        return False
    return user


async def get_current_user(
        session: SessionDep,
        token:str = Depends(oauth2_bearer)
):
    credentials_exception = HTTPException(status_code=401 ,detail="Could not validate credentials",headers={"WWW-Authenticate":"Bearer"},)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username:str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    user = get_user(session, username)
    if user is None:
        raise credentials_exception
    return user