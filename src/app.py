from zlib import DEF_BUF_SIZE
from db import db, User, Subject, Transaction, UserSubject
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

# APIs
@app.route("/")
def hello_world():
    """
    Default testing page
    """
    return json.dumps({"Status": "good"}), 200

# 1. Get all subjects (GET /api/subjects/)
@app.route("/api/subjects/", methods=["GET"])
def get_subjects():
    """
    Endpoint of getting all subjects and users in each subject
    """
    return success_response(
        {
            "subjects": [s.sub_serialize() for s in Subject.query.all()]
        }
    )

# 2. Create a user (POST /api/users/)
# {
#     "username": "zw332",

#     "name": "Zhan Wu" / null,
#     "bio": "Senior major in Math" / null,
#     "price": 10 / null,
#     "subject": ["Math", "Econ", "Chemistry"] / null,
#     "isAvailable": false / null
# }
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
    subjects = body.get("subject")
    isAvailable = body.get("isAvailable")

    if username is None:
        return failure_response("Username cannot be empty!", 400)
    
    new_user = User(username = username, name = name, bio = bio, price = price, isAvailable = isAvailable)
    db.session.add(new_user)
    user_id = new_user.sub_serialize()['id']

    for subject in subjects:
        subject_id = -1
        current_subject = Subject.query.filter_by(name = subject).first()
        if current_subject is None:
            new_subject = Subject(name = subject)
            db.session.add(new_subject)
            subject_id = new_subject.serialize()['id']
        else:
            subject_id = current_subject.serialize()['id']
        new_user_subject = UserSubject(user_id = user_id, subject_id = subject_id)
        db.session.add(new_user_subject)
    
    db.session.commit()
    return success_response(
        new_user.serialize(), 201
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)