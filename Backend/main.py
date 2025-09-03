from datetime import timedelta
from fastapi import FastAPI,Depends, HTTPException
from fastapi.security import  OAuth2PasswordRequestForm
from typing import Annotated, List
from sqlmodel import Session, select
from schema import ProductCreate, ProductRead, ProductUpdate, Token, UserRead 
from models import User, Product
from pydantic import EmailStr
from auth import authenticate_user, create_access_token, get_current_user
from db import engine, create_db_and_tables

ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]


app = FastAPI()

def not_found():
    raise HTTPException(status_code=404, detail="not found")
    

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


### Register new user into the system
@app.post("/signup", response_model=UserRead)
def signup(user_name:str, email:EmailStr, password:str, session:SessionDep, role:bool):
    existing_user = session.exec(select(User).where(User.user_name == user_name)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Usename already registered")
    user = User(user_name=user_name, email=email)
    user.set_password(password)
    user.set_role(role)
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



##################### admin previlages ###########

## Create product ++++
@app.post("/upload", response_model=ProductCreate)
def upload_product(
    session:SessionDep,
    title:str,
    description:str,
    price:float,
    stock:int,
    image:str,
    category:str, 
    ):
    product = Product(
        title=title,
        description=description,
        price=price,
        stock=stock,
        image=image,
        category=category
        )
    
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

# updating products

@app.put("/update/{id}", response_model=ProductCreate)
def update_product(id: int, product_update: ProductUpdate, session: SessionDep):
    product = session.exec(select(Product).where(Product.id == id)).first()
    if not product:
        not_found()

    # Only update the fields that were actually provided
    update_data = product_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    session.add(product)
    session.commit()
    session.refresh(product)

    return product


# deleting products

@app.delete("/delete/{id}")
def delete_product(session:SessionDep, id:int):
    product = session.get(Product, id)
    if  not product:
        not_found()
    
    session.delete(product)
    session.commit()
    return {"message":"product deleted successfully"}

# User previlages

@app.get("/products", response_model=List[ProductRead])
def get_all_products(session:SessionDep):
   product = session.exec(select(Product)).all()
   if not product:
       not_found()
   return product