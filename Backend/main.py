from datetime import datetime, timedelta
from fastapi import FastAPI,Depends, HTTPException
from fastapi.security import  OAuth2PasswordRequestForm
from typing import Annotated, List
from sqlmodel import Session, delete, select
from schema import ProductCreate, ProductRead, ProductUpdate, Token, UserRead 
from models import CartItems, Order, OrderItem, User, Product, Cart
from pydantic import EmailStr
from auth import authenticate_user, create_access_token, get_current_user
from db import engine, create_db_and_tables

ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]


app = FastAPI()

def not_found(item:str):
    raise HTTPException(status_code=404, detail=f"{item} not found")
    

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
        not_found("product")

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
        not_found("product")
    
    session.delete(product)
    session.commit()
    return {"message":"product deleted successfully"}

# User previlages

@app.get("/products", response_model=List[ProductRead])
def get_all_products(session:SessionDep):
   product = session.exec(select(Product)).all()
   if not product:
       not_found("product")
   return product

## Cart 
## add to cart

@app.post("/cart/{user_id}/add")
def add_to_cart(
    user_id:int,
    product_id:int,
    quantity:int,
    session:SessionDep
):
    user = session.get(User, user_id)
    if not user:
        not_found("user")


    product = session.get(Product, product_id)
    if not product:
        not_found("product")


    cart = session.exec(select(Cart).where(Cart.user_id == user_id)).first()
    if not cart:    # creates cart for user if not exist 
        cart = Cart(user_id = user_id)
        session.add(cart)
        session.commit()
        session.refresh(cart)

    cart_item = session.exec(
        select(CartItems).where(
            CartItems.cart_id == cart.id,
            CartItems.product_id == product_id
                                )
    ).first()

    if cart_item:
        cart_item.quantity += quantity
        cart_item.updated_at = datetime.utcnow()
    else:
        cart_item = CartItems(cart_id=cart.id, product_id = product_id, quantity=quantity)
        session.add(cart_item)

    session.commit()
    session.refresh(cart_item)

    return {"message": "Item added to cart", "cart_item": cart_item}

##view Cart 
@app.get("/cart/{user_id}/view")
def view_cart(user_id:int, session:SessionDep):
    cart = session.exec(select(Cart).where(Cart.user_id == user_id)).first()
    if not cart:
        not_found("cart")


    # getting all cart items

    cart_items = session.exec(select(CartItems, Product).join(Product,CartItems.product_id == Product.id).where(CartItems.cart_id == cart.id)).all()


   # format response
    items = []
    for cart_item, product in cart_items:
        items.append({
            "cart_item_id": cart_item.id,
            "product_id": product.id,
            "title": product.title,
            "price": product.price,
            "quantity": cart_item.quantity,
            "subtotal": product.price * cart_item.quantity        
        })

    total_price = sum(item["subtotal"] for item in items)

    return {
        "cart_id": cart.id,
        "user_id": cart.user_id,
        "items": items,
        "total_price": total_price
    }


@app.put("/cart/{user_id}/update/{product_id}")
def update_cart_item(
    user_id:int,
    product_id:int,
    quantity:int,
    session:SessionDep
):
    cart = session.exec(select(Cart).where(Cart.user_id == user_id)).first
    if not cart:
        not_found("cart")

    cart_item = session.exec(
        select(CartItems).where(
            CartItems.cart_id == Cart.id,
            CartItems.product_id == product_id
         )
    ).first()

    if not cart_item:
        not_found("cart items")

    if quantity <= 0:
        session.delete(cart_item)
        session.commit()
        return {"message":"Item removed from cart"}
    else:
        cart_item.quantity = quantity
        cart_item.updated_at = datetime.utcnow() if hasattr(cart_item, "updated_at") else cart_item.quantity
        session.add(cart_item)
        session.commit()
        session.refresh(cart_item)

        return {"message": "Item quantity updated", "cart_item": cart_item}
    

# placing orders and checking out

@app.post("/checkout/{user_id}")
def checkout(user_id: int, session:SessionDep):
    cart = session.exec(select(Cart).where(Cart.user_id == user_id)).first()
    if not cart:
        not_found("cart")
    
    cart_items = session.exec(
        select(CartItems, Product)
        .join(Product, CartItems.product_id == Product.id)
        .where(CartItems.cart_id == Cart.id)
    ).all()

    if not cart_items:
        not_found("cart items")

    total_amount = sum(product.price * cart_item.quantity for cart_item, product in cart_items)

    # create new order 

    order = Order(user_id=user_id, total_amount=total_amount, status="Pending")
    session.add(order)
    session.commit()
    session.refresh(order)

    # Adding order items

    for cart_item, product in cart_items:
        order_item = OrderItem(
            order_id = order.id,
            product_id=product.id,
            quantity=cart_item.quantity,
            price = product.price
        )
        session.add(order_item)


   ## clear cart after placing order
    session.exec(delete(CartItems).where(CartItems.cart_id == cart.id))
    session.commit()

    return {
        "message": "Order placed successfully",
        "order_id": order.id,
        "total_amount": total_amount,
        "status": order.status
    }

# get user oder
@app.get("/orders/{user_id}")
def get_orders(user_id:int, session:SessionDep):
    orders = session.exec(select(Order).where(Order.user_id == user_id)).all()
    if not orders:
        not_found("orders")
    return orders


@app.get("/orders/{order_id}/items")
def get_order_items(order_id:int, session:SessionDep):
    order_items = session.exec(
        select(OrderItem, Product)
        .join(Product, OrderItem.product_id == Product.id)
        .where(OrderItem.order_id == order_id)).all()
    
    if not order_items:
        not_found("Items")

    return [
        {
            "product_id": product.id,
            "title": product.title,
            "price": order_item.price,
            "quantity": order_item.quantity,
            "subtotal": order_item.price * order_item.quantity
        }
        for order_item, product in order_items
    ]

# user order history
@app.get("/order-history/{user_id}")
def get_order_history(user_id:int, session:SessionDep):

    orders = session.exec(select(Order).where(Order.user_id == user_id)).all()
    if not orders:
        not_found("orders")
    
    history = []

    for order in orders:
        order_items = session.exec(
            select(OrderItem, Product)
            .join(Product, OrderItem.product_id == Product.id)
            .where(OrderItem.order_id == order.id)
        ).all()

        items_list = [
            {
                "product_id":product.id,
                "title":product.title,
                "price":order_item.price,
                "quantity":order_item.quantity,
                "subtotal":order_item.price * order_item.quantity
            }
            for order_item, product in order_items
        ]

        history.append({
            "order_id": order.id,
            "total_amount": order.total_amount,
            "status": order.status,
            "created_at": order.created_at,
            "items": items_list           
        })

    
    return {"user_id": user_id, "order_history": history}

