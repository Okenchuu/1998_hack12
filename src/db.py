import datetime
from distutils.cygwinccompiler import Mingw32CCompiler
import hashlib
import os

import bcrypt
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# classes here

userSubject_table = db.Table(
    "userSubject",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("subject_id", db.Integer, db.ForeignKey("subject.id"))
)

class User(db.Model):
    """
    User model
    """
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key = True)
    subjects = db.relationship("Subject", secondary = userSubject_table, back_populates="users")  
    # User information
    username = db.Column(db.String, nullable=False, unique=True)
    name = db.Column(db.String, nullable=True)
    bio = db.Column(db.String, nullable=True)
    price = db.Column(db.Integer, nullable=True)
    isAvailable = db.Column(db.Boolean, nullable=True)
    sent_transactions = db.relationship(
        "Transaction",
        foreign_keys= '[transaction.c.sender_id]',
        back_populates="sender",
        cascade="all, delete",
    )
    received_transactions = db.relationship(
        "Transaction",
        foreign_keys= '[transaction.c.receiver_id]',
        back_populates="receiver",
        cascade="all, delete",
    )
    password_digest = db.Column(db.String, nullable=False)
    # Session information
    session_token = db.Column(db.String, nullable=False, unique=True)
    session_expiration = db.Column(db.DateTime, nullable=False)
    update_token = db.Column(db.String, nullable=False, unique=True)
    
    def __init__(self, **kwargs):
        """
        Initializes a User object
        """
        self.username = kwargs.get("username")
        self.name = kwargs.get("name")
        self.bio = kwargs.get("bio")
        self.price = kwargs.get("price")
        self.isAvailable = kwargs.get("isAvailable")
        self.password_digest = bcrypt.hashpw(kwargs.get("password").encode("utf8"), bcrypt.gensalt(rounds=13))
        self.renew_session()
        
    def serialize(self):
        """
        Serialize a User object
        """
        return {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "bio": self.bio,
            "price": self.price,
            "isAvailable": self.isAvailable,
            "subject": [s.sub_serialize() for s in self.subjects],
            "sent_transactions": [s.serialize() for s in self.sent_transactions],
            "received_transactions": [s.serialize() for s in self.received_transactions]
        }
    
    def sub_serialize(self):
        """
        Sub-serialize a Users object
        """
        return {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "bio": self.bio,
            "price": self.price,
            "isAvailable": self.isAvailable
        }
    
    def update_profile(self,bio, price, isAvailable):
        """
        Updating a user's profile
        """
        self.bio = bio
        self.price = price
        self.isAvailable = isAvailable
        
    def _urlsafe_base_64(self):
        """
        Randomly generates hashed tokens (used for session/update tokens)
        """
        return hashlib.sha1(os.urandom(64)).hexdigest()

    def renew_session(self):
        """
        Renews the sessions, i.e.
        1. Creates a new session token
        2. Sets the expiration time of the session to be a day from now
        3. Creates a new update token
        """
        self.session_token = self._urlsafe_base_64()
        self.session_expiration = datetime.datetime.now() + datetime.timedelta(days=1)
        self.update_token = self._urlsafe_base_64()

    def verify_password(self, password):
        """
        Verifies the password of a user
        """
        return bcrypt.checkpw(password.encode("utf8"), self.password_digest)

    def verify_session_token(self, session_token):
        """
        Verifies the session token of a user
        """
        return session_token == self.session_token and datetime.datetime.now() < self.session_expiration

    def verify_update_token(self, update_token):
        """
        Verifies the update token of a user
        """
        return update_token == self.update_token
    
def create_user(username, name, bio, price, password, isAvailable):
    """
    Create a new user through register
    """
    existing_user = User.query.filter_by(username = username).first()
    if existing_user:
        return False, None
    user = User(username = username, name = name, bio = bio, price = price, password = password, isAvailable = isAvailable)
    db.session.add(user)
    db.session.commit()
    return True, user
        
def verify_credentials(username, password):
    """
    Verify credentials for logging in
    """       
    existing_user = User.query.filter_by(username = username).first()
    if not existing_user:
        return False, None
    return existing_user.verify_password(password), existing_user

def renew_session(update_token):
    existing_user = User.query.filter_by(update_token = update_token).first()
    if not existing_user:
        return False, None
    existing_user.renew_session()
    db.session.commit()
    return True, existing_user

def verify_session(session_token):
    return User.query.filter_by(session_token = session_token).first()

class Subject(db.Model):    
    __tablename__ = "subject"    
    id = db.Column(db.Integer, primary_key=True)
    users = db.relationship("User", secondary = userSubject_table, back_populates="subjects")
    name = db.Column(db.String, nullable=False)
    
    def __init__(self, **kwargs):
        """
        Initializes a Subject object
        """
        self.name = kwargs.get("name")
    
    def serialize(self):
        """
        Serialize a Subject object
        """
        return {
            "id": self.id,
            "name": self.name,
            "users": [s.sub_serialize() for s in self.users]  
        }
        
    def sub_serialize(self):
        """
        Sub-serialize a Subject object
        """
        return {
            "id": self.id,
            "name": self.name
        }



class Transaction(db.Model):
    """
    Transaction model
    """
    __tablename__ = "transaction"
    id = db.Column(db.Integer, primary_key = True)
    status = db.Column(db.String, nullable = False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False)
    sender = db.relationship("User", foreign_keys = [sender_id], back_populates="sent_transactions")
    receiver = db.relationship("User", foreign_keys = [receiver_id], back_populates="received_transactions")


    def __init__(self, **kwargs):
        """
        Initializes a Transaction object
        """
        self.status = kwargs.get("status")
        self.sender_id = kwargs.get("sender_id")
        self.receiver_id = kwargs.get("receiver_id")

    def serialize(self):
        """
        Serializes a Transaction object
        """    
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "status": self.status
        }

# class UserSubject(db.Model):
#     __tablename__ = "userSubject"
#     id = db.Column(db.Integer, primary_key=True)    
#     user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
#     subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=False)
#     user = db.relationship("User", back_populates="user_subject")
#     subject = db.relationship("Subject", back_populates="user_subject")
    
#     def __init__(self, **kwargs):
#         """
#         Initializes a UserSubject object
#         """
#         self.user_id = kwargs.get('user_id')
#         self.subject_id = kwargs.get('subject_id')
    
#     def serialize_users(self):
#         """
#         Serialize the user column
#         """
#         return self.user.sub_serialize()

#     def serialize_subjects(self):
#         """
#         Serialize the subject column
#         """
#         return self.subject.sub_serialize()
    


