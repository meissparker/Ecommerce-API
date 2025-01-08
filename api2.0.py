from __future__ import annotations 
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy import ForeignKey, Table, Column, String, Integer, select, DateTime
from marshmallow import ValidationError
from typing import List, Optional
from datetime import date

# Initialize Flask app
app = Flask(__name__)

# MySQL database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Kronos123@localhost/ecommerce_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Creating the Base Model
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy and Marshmallow
db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)

# Association Tables

order_product = Table( 
    "order_product",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True)
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200), unique=True)

    orders: Mapped[List["Order"]] = relationship(back_populates="users")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    order_day: Mapped[str] = mapped_column(default=date.today, nullable=False)


    products: Mapped[List["Product"]] = relationship("Product", secondary=order_product, back_populates="orders")
    users: Mapped["User"] = relationship(back_populates="orders")

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column()

    orders: Mapped[List["Order"]] = relationship("Order", secondary=order_product, back_populates="products")


# User Schema
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product

       
       
# Initialize Schemas
user_schema = UserSchema()
users_schema = UserSchema(many=True) 
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)



#Routes

#Create User
@app.route('/users', methods=['POST'])
def create_user():
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_user = User(name=user_data['name'], email=user_data['email'], address=user_data['address'])
    db.session.add(new_user)
    db.session.commit()

    return user_schema.jsonify(new_user), 201


#Read all users
@app.route('/users', methods=['GET'])
def get_users():
    query = select(User)
    users = db.session.execute(query).scalars().all()

    return users_schema.jsonify(users), 200


#Read single user by id
@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = db.session.get(User, id)
    return user_schema.jsonify(user), 200


#Update User
@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = db.session.get(User, id)

    if not user:
        return jsonify({"message": "Invalid user id"}), 400
    
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    user.name = user_data['name']
    user.email = user_data['email']
    user.address = user_data['address']

    db.session.commit()
    return user_schema.jsonify(user), 200


#Delete User
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = db.session.get(User, id)

    if not user:
        return jsonify({"message": "Invalid user id"}), 400
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"succefully deleted user {id}"}), 200


#Create Order
@app.route('/orders', methods=['POST'])
def order():
    try:
        order_data = order_schema.load(request.json)
        print(order_data)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_order = Order(user_id=order_data['id'])
    print(new_order)
    db.session.add(new_order)
    db.session.commit()

    return order_schema.jsonify(new_order), 201


# Add Product to an Order
@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['GET'])
def connect_product(order_id, product_id):
    order = db.session.get(Order, order_id)
    product = db.session.get(Product, product_id)

    order.products.append(product)
    db.session.commit()
    return jsonify({"message":f"{product.product_name} has been added to order {order_id}."}), 200


# Show all orders for a user by ID
@app.route("/user/my_orders/<int:user_id>", methods=['GET'])
def show_orders(user_id):
    user = db.session.get(User, user_id)
    return users_schema.jsonify(user.orders), 200

# Show all products for an order by ID
@app.route("/orders/<int:order_id>/products", methods=['GET'])
def show_products(order_id):
    order = db.session.get(Order, order_id)
    return products_schema.jsonify(order.products), 200


#Remove a product from an order
@app.route('/orders/<int:order_id>/remove_product/<int:product_id>', methods=['DELETE'])
def remove_product(order_id, product_id):
    order = db.session.get(Order, order_id)
    product = db.session.get(Product, product_id)
    
    order.products.remove(product)
    db.session.commit()
    return jsonify({"message": f"Succefully deleted product {product_id},{product.product_name} from order {order_id}"}), 200



#Create Products
@app.route('/products', methods=['POST'])
def create_products():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_product = Product(product_name=product_data['product_name'], price=product_data['price'])
    db.session.add(new_product)
    db.session.commit()

    return product_schema.jsonify(new_product), 201


# Read all products
@app.route('/products', methods=['GET'])
def get_products():
    query = select(Product)
    products = db.session.execute(query).scalars().all()

    return products_schema.jsonify(products), 200


#Read Single Product by ID
@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = db.session.get(Product, id)
    return product_schema.jsonify(product), 200


#Update Product by ID
@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = db.session.get(Product, id)

    if not product:
        return jsonify({"message": "Invalid product id"}), 400
    
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    product.product_name = product_data['product_name']
    product.price = product_data['price']

    db.session.commit()
    return product_schema.jsonify(product), 200


#Delete Product by ID
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = db.session.get(Product, id)

    if not product:
        return jsonify({"message": "Invalid product id"}), 400
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": f"succefully deleted product {id}, {product.product_name}"}), 200



if __name__ == "__main__":

    with app.app_context():

        db.create_all()

    app.run(debug=True)