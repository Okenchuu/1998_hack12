from zlib import DEF_BUF_SIZE

from sqlalchemy import false
from db import db, User, Subject, Transaction, create_user, verify_credentials, renew_session, verify_session
from flask import Flask, request
import json
import os


app = Flask(__name__)
db_filename = "tutor.db"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()

def success_response(data, code=200):
    return json.dumps(data), code


def failure_response(message, code=404):
    return json.dumps({"error": message}), code

def extract_token(request):
    token = request.headers.get("Authorization")
    if token is None:
        return False, "Missing authorization header"
    token = token.replace("Bearer","").strip()
    return True, token

# APIs
@app.route("/")
def hello_world():
    """
    Default testing page
    """
    return json.dumps({"Status": "good"}), 200

# -- SUBJECT ------------------------------------------------------
@app.route("/api/subjects/", methods=["GET"])
def get_subjects():
    """
    Endpoint of getting all subjects id and names
    """
    return success_response(
        {
            "subjects": [s.sub_serialize() for s in Subject.query.all()]
        }
    )

    
@app.route("/api/subjects/<int:subject_id>/users/", methods=["GET"])
def get_users_in_subject(subject_id):
    """
    Endpoint for getting all available tutors in a subject
    """
    subject = Subject.query.filter_by(id=subject_id).first()
    if subject is None:
        return failure_response("Subject not found!")
    users = subject.serialize()["users"]
    res = []
    for user in users:
        if bool(user.get("isAvailable")):
            res.append(user)
    return success_response(res)


# -- USER ------------------------------------------------------
@app.route("/api/users/", methods=["POST"])
def create_users():
    """
    Endpoint of creating a new user
    """
    body = json.loads(request.data)
    username = body.get("username")
    name = body.get("name")
    bio = body.get("bio")
    price = body.get("price")
    subjects = body.get("subjects")
    password = body.get("password")
    isAvailable = bool(false)
    if username is None or name is None or bio is None or price is None or subjects is None or password is None:
        return failure_response("user info input missing", 400)
    
    if len(username) == 0:
        return failure_response("Username cannot be empty!", 400)
    if len(password) == 0:
        return failure_response("password cannot be empty!", 400)
    
    created, user = create_user(username, name, bio, price, password, isAvailable)
    if not created:
        return failure_response("User already exist!", 403)

    if subjects is not None:
        for subject in subjects:
            current_subject = Subject.query.filter_by(name = subject).first()
            if current_subject is None:
                current_subject = Subject(name = subject)
                db.session.add(current_subject)
            user.subjects.append(current_subject)    

    db.session.commit()
    return success_response({
        "session_token": user.session_token,
        "session_expiration": str(user.session_expiration),
        "update_token": user.update_token,
        "user": user.serialize()
    })

  
@app.route("/api/users/", methods=["GET"])
def get_all_users():
    """
    Endpoint of getting all users
    """
    users = [u.serialize() for u in User.query.all()]
    return success_response({"users":users})


@app.route("/api/users/<int:user_id>/")
def get_user_by_id(user_id):
    """
    Endpoint for getting a specific user by id
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    return success_response(user.serialize())


@app.route("/api/users/<int:user_id>/", methods=["POST"])
def update_user_by_id(user_id):
    """
    Endpoint for updating a specific user's profile by id
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    body = json.loads(request.data)
    bio = body.get("bio")
    price = body.get("price")
    subjects = body.get("subject")
    isAvailable = bool(body.get("isAvailable"))
    if bio is None or price is None or subjects is None or isAvailable is None:
        return failure_response("user info input missing", 400)
    
    user.update_profile(bio, price, isAvailable)
    user.subjects = []
    db.session.commit()   
    # Math, Econ, Physics
    # [Math, Econ, Physics]
    # [Math] 
 
    for subject in subjects:
            current_subject = Subject.query.filter_by(name = subject).first()
            if current_subject is None:
                current_subject = Subject(name = subject)
                db.session.add(current_subject)
            user.subjects.append(current_subject) 
    db.session.commit()
    return success_response(user.serialize())



@app.route("/api/users/<int:user_id>/", methods=["DELETE"])
def delete_user(user_id):
    """
    Endpoint for deleting a specific user by id
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    res = user.serialize()
    db.session.delete(user)
    db.session.commit()
    return success_response(res)



# -- AUTHENTICATION ------------------------------------------------------
@app.route("/api/login/", methods=["POST"])
def login():
    """
    Endpoint of logging in
    """
    body = json.loads(request.data)
    username = body.get("username")
    password = body.get("password")
    if username is None or password is None:
        return failure_response("Invalid username or password!", 400)
    valid_creds, user = verify_credentials(username, password)
    
    if not valid_creds:
        return failure_response("Invalid username or password!")
    return success_response({
        "session_token": user.session_token,
        "session_expiration": str(user.session_expiration),
        "update_token":user.update_token
    })
    
@app.route("/api/session/", methods=["POST"])
def update_session():
    """
    Endpoint of updating session
    """
    success, update_token = extract_token(request)
    if not success:
        return failure_response(update_token)
    valid, user = renew_session(update_token)
    if not valid:
        return failure_response("Invalid update token")
    return success_response({
        "session_token": user.session_token,
        "session_expiration": str(user.session_expiration),
        "update_token":user.update_token
    })

@app.route("/api/secret/", methods=["GET"])
def secret_message():
    """
    Endpoint of secret message
    """
    success, session_token = extract_token(request)
    if not success:
        return failure_response(session_token)
    valid = verify_session(session_token)
    if not valid:
        return failure_response("Invalid session token")
    return success_response("Hello World")  
      

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)