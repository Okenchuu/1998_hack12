import datetime
from distutils.cygwinccompiler import Mingw32CCompiler
import hashlib
import os

import bcrypt
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# classes here

class Users(db.Model):
    """
    Users model
    """
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True)
    user_subject = db.relationship("UserSubject", back_populates="user")  
    # User information
    username = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    bio = db.Column(db.String, nullable=True)
    contactInfo = db.Column(db.String, nullable=True)
    minPrice = db.Column(db.Integer, nullable=True)
    maxPrice = db.Column(db.Integer, nullable=True)
    isAvailable = db.Column(db.Boolean, nullable=True)
    password_digest = db.Column(db.String, nullable=False)
    # Session information
    session_token = db.Column(db.String, nullable=False, unique=True)
    session_expiration = db.Column(db.DateTime, nullable=False)
    update_token = db.Column(db.String, nullable=False, unique=True)
    
    def __init__(self, **kwargs):
        """
        Initializes a Users object
        """
        self.username = kwargs.get("username")
        self.name = kwargs.get("name")
        self.bio = kwargs.get("bio")
        self.contactInfo = kwargs.get("contactInfo")
        self.minPrice = kwargs.get("minPrice")
        self.maxPrice = kwargs.get("maxPrice")
        self.isAvailable = kwargs.get("isAvailable")
        self.password_digest = bcrypt.hashpw(kwargs.get("password").encode("utf8"), bcrypt.gensalt(rounds=13))
        
    def serialize(self):
        """
        Serialize a Users object
        """
        return {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "bio": self.bio,
            "contactInfo": self.contactInfo,
            "minPrice": self.minPrice,
            "maxPrice": self.maxPrice,
            "isAvailable": self.isAvailable,
            "subject": [s.serialize_subjects() for s in self.user_subject]
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
            "contactInfo": self.contactInfo,
            "minPrice": self.minPrice,
            "maxPrice": self.maxPrice,
            "isAvailable": self.isAvailable
        }
    
    def update_profile(self, **kwargs):
        """
        Updating a Users object's column data, used for editing a user's profile
        """
        self.username = kwargs.get("username")
        self.name = kwargs.get("name")
        self.bio = kwargs.get("bio")
        self.contactInfo = kwargs.get("contactInfo")
        self.minPrice = kwargs.get("minPrice")
        self.maxPrice = kwargs.get("maxPrice")
        self.isAvailable = kwargs.get("isAvailable")
        
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
        
        
    
    
class Subjects(db.Model):    
    __tablename__ = "subjects"    
    id = db.Column(db.Integer, primary_key=True)
    user_subject = db.relationship("UserSubject", back_populates="subject") 
    name = db.Column(db.String, nullable=False)
    
    def __init__(self, **kwargs):
        """
        Initializes a Subjects object
        """
        self.name = kwargs.get("name")
    
    def serialize(self):
        """
        Serialize a Subjects object
        """
        return {
            "id": self.id,
            "name": self.name,
            "users": [s.serialize_users() for s in self.user_subject]  
        }
        
    def sub_serialize(self):
        """
        Sub-serialize a Subjects object
        """
        return {
            "id": self.id,
            "name": self.name
        }



class UserSubject(db.Model):
    __tablename__ = "usersubject"
    id = db.Column(db.Integer, primary_key=True)    
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    user = db.relationship("Users", back_populates="user_subject")
    subject = db.relationship("Subjects", back_populates="user_subject")
    
    def __init__(self, **kwargs):
        """
        Initializes a UserSubjects object
        """
        self.user_id = kwargs.get('user_id')
        self.subject_id = kwargs.get('subject_id')
    
    def serialize_users(self):
        """
        Serialize the user column
        """
        return self.user.sub_serialize()

    def serialize_subjects(self):
        """
        Serialize the subject column
        """
        return self.subject.sub_serialize()
    