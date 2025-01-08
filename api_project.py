from __future__ import annotations
from flask import Flask, request, jsonify 
from flask_sqlalchemy import SQLAlchemy 
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy import ForeignKey, Table, Column, String, Integer, select
from marshmallow import ValidationError
from typing import List, Optional


# Initialize Flask app
app = Flask(__name__)

# MySQL database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Kronos123@localhost/flask_api_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Creating our Base Model
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy and Marshmallow
db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)

# Association Table
user_pet = Table( 
    "user_pet",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("pet_id", ForeignKey("pets.id"), primary_key=True)
)

# Models
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200))

    #One-to-Many relationship from this User to a List of Pet Objects
    pets: Mapped[List["Pet"]] = relationship("Pet", secondary=user_pet, back_populates="owners")

class Pet(Base):
    __tablename__ = "pets"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    animal: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # One-to-Many relationship, One pet can be related to a List of Users
    owners: Mapped[List["User"]] = relationship("User", secondary=user_pet, back_populates="pets")

#app.py

# User Schema
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        
# Pet Schema
class PetSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Pet
       
       
# Initialize Schemas
user_schema = UserSchema()
users_schema = UserSchema(many=True) #Can serialize many User objects (a list of them)
pet_schema = PetSchema()
pets_schema = PetSchema(many=True)

#Routes

#Create User
@app.route('/users', methods=['POST'])
def create_user():
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_user = User(name=user_data['name'], email=user_data['email'])
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


#Create Pet 
@app.route('/pets', methods=['POST'])
def create_pet():
    try:
        pet_data = pet_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_pet = Pet(name=pet_data['name'], animal=pet_data['animal'])
    db.session.add(new_pet)
    db.session.commit()

    return pet_schema.jsonify(new_pet), 201

#Associate Single Pet with a User
@app.route('/users/<int:user_id>/add_pet/<int:pet_id>', methods=['GET'])
def adopt_pet(user_id, pet_id):
    user = db.session.get(User, user_id)
    pet = db.session.get(Pet, pet_id)

    user.pets.append(pet)
    db.session.commit()
    return jsonify({"message":f"{user.name} adopted the {pet.animal}, {pet.name}!"}), 200

#Associate Multiple Pets with a User
@app.route('/users/<int:user_id>/add_pets', methods=['POST'])
def add_pets(user_id):
    user = db.session.get(User, user_id)
    pet_data = request.json

    for id in pet_data['pet_ids']:
        pet = db.session.get(Pet, id)
        user.pets.append(pet)
        db.session.commit()

    return jsonify({"message": "All pets added!"}), 200

#Show User Pets
@app.route("/users/my_pets/<int:user_id>", methods=['GET'])
def my_pets(user_id):
    user = db.session.get(User, user_id)
    return pets_schema.jsonify(user.pets), 200



if __name__ == "__main__":

    with app.app_context():

        db.create_all()

    app.run(debug=True)
