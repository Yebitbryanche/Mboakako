from sqlmodel import SQLModel, Field
from pydantic import EmailStr
from passlib.context import CryptContext
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated='auto')


class User(SQLModel, table=True):
    __tablename__="User"


    id:int = Field(primary_key=True,default=None)
    user_name: str = Field(index=True)
    email: EmailStr = Field(index=True)
    password_hash: str = Field(index=True)
    role: str = Field(index=True)

    def set_password(self, password:str):
        self.password_hash = pwd_context.hash(password)
     
     #code block to verify user password during login
    def check_password(self, password:str) -> bool:
        return pwd_context.verify(password, self.password_hash)
    
## product table
class Product(SQLModel, table=True):
    __tablename__ = "Product"

    id:int = Field(primary_key=True, default=None)
    title:str = Field(index=True)
    description: str = Field(index=True)
    price: float = Field(index=True)
    stock: int 
    image: str  
    category: str
    created_at : datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)



## review table
class Review(SQLModel, table=True):
    __tablename__ = "Reviews"

    id:int = Field(primary_key=True)
    user_id:int = Field(foreign_key=("User.id"))
    product_id:int = Field(foreign_key="Product.id")
    rating:int
    comment:str
    created_at:datetime = Field(default_factory=datetime.utcnow)



## shopping cart table
class Cart(SQLModel, table=True):
    __tablename__ = "Cart"

    id:int = Field(primary_key=True, default=None)
    user_id = Field(foreign_key= "User.id")
    created_at : datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


## cart items table
class CartItems(SQLModel, table=True):
    __tablename__ = "CartItems"

    id:int = Field(primary_key=True, default=None)
    cart_id:int = Field(foreign_key=("Cart.id"))
    product_id:int = Field(foreign_key=("Product.id"))
    quantity:int = Field(default=1)

    

## Order table
class Order(SQLModel, table=True):
    __tablename__ = "Order"

    id:int = Field(primary_key=True)
    user_id:int = Field(foreign_key=("User.id"))
    total_amount:float 
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)



## Order Items
class OrderItem(SQLModel, table=True):
    __tablename__ = "OrderItem"


    id:int = Field(primary_key=True)
    product_id: int = Field(foreign_key="Product.id")
    order_id:int = Field(foreign_key=("Order.id")) 
    quantity:int
    price:float

## user Activity Table for AI model

class UserActivity(SQLModel, table=True):
    id:int = Field(primary_key=True)
    user_id:int = Field(foreign_key=("User.id"))
    product_id:int = Field(foreign_key=("Product.id"))
    created_at: datetime = Field(default_factory=datetime.utcnow)


